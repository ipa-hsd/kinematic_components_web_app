from ament_index_python.packages import get_package_share_directory
from bigtree import dict_to_tree, str_to_tree, print_tree, tree_to_dot
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
import json
import os
import uuid

app = Flask(__name__, static_folder='static', template_folder='templates')

# /// = relative path, //// = absolute path
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

socketio = SocketIO(app, async_mode=None, logger=True, engineio_logger=True)

class Node:
    def __init__(self, name, attributes=None, children=None):
        self.name = name
        self.attributes = attributes or {}
        self.children = children or []

class Component(db.Model):
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String(100))
    category = db.Column(db.String(100))
    repo = db.Column(db.String(100))
    branch = db.Column(db.String(100))
    package = db.Column(db.String(100))
    version = db.Column(db.String(100))
    image_file = db.Column(db.String(500))
    model = db.Column(db.JSON())

    def generate_tree_html(self):
        # Assuming you have a tree represented by a Node object stored in self.model
        root = dict_to_tree(self.model)
        tree_html = f'<ul>{convert_node_to_html(root)}</ul>'
        return tree_html

    def generate_tree_html(self):
        # Assuming you have a tree represented by a Node object stored in self.model
        root = dict_to_tree(self.model)
        tree_html = f'<ul>{convert_node_to_html(root)}</ul>'
        return tree_html


with app.app_context():
    db.create_all()


def get_components_all():
    return db.session.query(Component).all()


# this is ideally come from ament
# def get_package_share_directory(package_name):
#     path = '/moveit_ws/install/' + package_name + '/share/'
#     print(path)
#     return path


@app.get("/")
def home():
    component_list = get_components_all()
    return render_template("base.html", component_list=component_list)

def convert_node_to_html(node):
    html = f'<li>{node.name}'

    if node.attributes:
        html += '<ul>'
        for key, value in node.attributes.items():
            html += f'<li>{key}: {value}</li>'
        html += '</ul>'

    if node.children:
        html += '<ul>'
        for child in node.children:
            html += convert_node_to_html(child)
        html += '</ul>'

    html += '</li>'
    return html

@app.route("/view_tree/<component_id>")
def view_tree(component_id):
    component = Component.query.get_or_404(component_id)
    tree_html = component.generate_tree_html()
    return render_template('view_tree.html', component=component, tree_html=tree_html)

@app.route("/add", methods=["POST"])
def add():
    data = json.loads(request.form["model"])["component"]
    data['id'] = str(uuid.uuid4())

    dot_trees = json.loads(request.form["dot_trees"])

    robot_name = ''
    if data['name'] == '':
        robot_name = 'component'
    else:
        robot_name = data['name']

    image_files = ''
    for name, tree in dot_trees.items():
        root = dict_to_tree(tree)

        filepath = 'kinematic_components_web_app/static/images/' + data['gitRepo']['package']
        if not filepath.endswith('/'):
            filepath += '/'
        filepath += robot_name + '/'
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        dot_file = tree_to_dot(root)
        image_path = filepath + name + '.png'
        dot_file.write_png(image_path)

        image_files += '/' + image_path + ';'

        json_trees.append(tree)
    
    # model = json.loads(request.form["model"])
    valid_json_string = str(json_trees).replace("'", "\"")
    tree_html = f'<ul>{convert_node_to_html(root)}</ul>'
    component = Component(id=data['id'], name=data['name'],
                          category=data['category'],
                          repo=data['gitRepo']['repo'],
                          branch=data['gitRepo']['branch'],
                          package=data['gitRepo']['package'],
                          version=data['gitRepo']['version'],
                          image_file=image_files,
                          model=data)

    db.session.add(component)
    db.session.commit()
    emit('add component', data, namespace='/test', broadcast=True)
    return redirect(url_for("home"))



@app.get("/components/<string:component_cat>/<string:component_id>")
def components(component_cat, component_id):
    component = db.session.query(Component).filter(
        Component.id == component_id).first()

    image_files = component.image_file.split(';')[:-1]

    return render_template("component.html", component=component, image_files=image_files)


@app.get("/delete/<string:component_id>")
def delete(component_id):
    component = db.session.query(Component).filter(
        Component.id == component_id).first()
    db.session.delete(component)
    db.session.commit()
    return redirect(url_for("home"))


@socketio.on('connect', namespace='/component_view')
def test_connect():
    print('Client connected')


@socketio.on('component id', namespace='/viz')
def handle_message(msg):
    component_id = msg['data'].split('/')[-1]
    component = db.session.query(Component).filter(
        Component.id == component_id).first()

    package_path = get_package_share_directory(component.package)

    emit('viz model', [component.model, component.repo, component.branch, component.version, component.package, package_path,
         component_id], namespace='/viz', broadcast=True)


@socketio.on('get mesh', namespace='/component_view')
def get_mesh_path(msg):
    mesh_path = msg['data'].lstrip('package').lstrip('://')
    package = mesh_path.split('/')[0]
    abs_package_path = get_package_share_directory(package)
    rel_mesh_path = mesh_path.lstrip(package)
    abs_mesh_path = abs_package_path + rel_mesh_path

    with open(abs_mesh_path, 'rb') as f:
        emit('mesh file', {'data': f.read()})

if __name__ == '__main__':
    socketio.run(app)
