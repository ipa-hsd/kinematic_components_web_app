class Node:
    def __init__(self, name, attributes=None, children=None):
        self.name = name
        self.attributes = attributes or {}
        self.children = children or []

def convert_node_to_html(node):
    html = f'<div class="node">{node.name}'
   
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
   
    html += '</div>'
    return html