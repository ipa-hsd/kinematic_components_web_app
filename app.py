from ament_index_python.packages import get_package_share_directory
from bigtree import dict_to_tree, str_to_tree, print_tree, tree_to_dot
from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
import json
import os
import uuid
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from io import BytesIO
import base64

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

def dictionary_to_tree(path, attributes):
    components = path.split('/')
    root = Node(components[1], attributes={**attributes, "path": components[1]})
    current_node = root

    for component in components[2:]:
        child = Node(component, attributes={"path": current_node.attributes["path"] + "/" + component})
        current_node.children.append(child)
        current_node = child

    return root

def convert_json_to_tree(json_data):
    root = None

    for path, attributes in json_data[0].items():
        root = dictionary_to_tree(path, attributes)

    return root

def convert_node_to_graph(node, graph=None, parent_name=None, pos=None, level=0, width=2., vert_gap=0.4, xcenter=0.5):
    if graph is None:
        graph = nx.DiGraph()
    if pos is None:
        pos = {node.name: (xcenter, 1 - level * vert_gap)}
    else:
        pos[node.name] = (xcenter, 1 - level * vert_gap)
    neighbors = list(graph.neighbors(parent_name)) + [parent_name] if parent_name is not None else []
    if parent_name is not None:
        neighbors.remove(node.name)
    if len(neighbors) != 0:
        dx = width / 2
        nextx = xcenter - width / 2 - dx / 2
        for neighbor in neighbors:
            nextx += dx
            pos = convert_node_to_graph(node, graph=graph, parent_name=neighbor, pos=pos, level=level + 1,
                                        width=dx, xcenter=nextx)
    return pos

def visualize_tree(node):
    graph = nx.DiGraph()
    pos = convert_node_to_graph(node, graph=graph)
    fig, ax = plt.subplots()
    nx.draw(graph, pos=pos, with_labels=True, arrows=False, node_size=700, font_size=8, font_color='white',
            node_color='skyblue')
    canvas = FigureCanvas(fig)
    '''plt.savefig(img_data, format="png", bbox_inches = 'tight', pad_inches = 0.1)'''
    img_data = BytesIO()
    canvas.print_png(img_data)
    '''img_data.seek(0)'''
    plt.close(fig)
    img_data_base64 = base64.b64encode(img_data.read()).decode('utf-8')
    return img_data_base64

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
    json_trees = component.json_trees
    root_node = convert_json_to_tree(json_trees)
    image_file = visualize_tree(root_node)
    tree_html = f'<ul>{convert_node_to_html(root_node)}</ul>'

    return render_template("component.html", component=component, image_file=image_file,tree_data=json_trees, tree_html=tree_html)


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
