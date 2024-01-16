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
    json_trees = db.Column(db.JSON())


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

    if node.children:
        html += '<ul>'
        for child in node.children:
            html += convert_node_to_html(child)
        html += '</ul>'

    html += '</li>'
    return html


def convert_json_to_tree(json_data):
    root = Node("Root")  # Create a root node to hold all components

    for tree_data in json_data:
        for path, attributes in tree_data.items():
            components = path.split('/')
            current_node = root

            for component in components[1:]:
                child = next((child for child in current_node.children if child.name == component), None)

                if not child:
                    child = Node(component)
                    current_node.children.append(child)

                current_node = child

    return root


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

    json_trees = []
    root = None
    for name, tree in dot_trees.items():
        root = dict_to_tree(tree)
        json_trees.append(tree)
    
    if root:
        # model = json.loads(request.form["model"])
        # TODO: assuming that only tree exists in dot_trees
        valid_json_string = str(json_trees).replace("'", "\"")
        tree_html = f'<ul>{convert_node_to_html(root)}</ul>'
        component = Component(id=data['id'], name=data['name'],
                            category=data['category'],
                            repo=data['gitRepo']['repo'],
                            branch=data['gitRepo']['branch'],
                            package=data['gitRepo']['package'],
                            version=data['gitRepo']['version'],
                            model=data,
                            json_trees=json_trees)

        db.session.add(component)
        db.session.commit()
        emit('add component', data, namespace='/test', broadcast=True)

    return redirect(url_for("home"))


@app.get("/components/<string:component_cat>/<string:component_id>")
def components(component_cat, component_id):
    component = db.session.query(Component).filter(
        Component.id == component_id).first()

    json_trees = component.json_trees
    root_node = convert_json_to_tree(json_trees)
    tree_html = f'<ul>{convert_node_to_html(root_node)}</ul>'

    return render_template("component.html", component=component, tree_data=json_trees, tree_html=tree_html)


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

    try:
        package_path = get_package_share_directory(component.package)
        package_path = package_path.replace('/app/kinematic_components_web_app/', '')
        package_path = package_path.rstrip(component.package)

        emit('viz model', [component.model, package_path], namespace='/viz', broadcast=True)
    except Exception as ex:
        print(repr(ex))


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
