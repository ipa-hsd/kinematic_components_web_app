var viewer = undefined;

function init() {
    viewer = new ROS3D.Viewer({
        divID: 'urdf',
        width: 800,
        height: 600,
        antialias: true
    });

    // Add a grid.
    viewer.addObject(new ROS3D.Grid({ color: '#303030' }));
}

function addMesh(filename, repoPath, origin) {
    const colorMaterial = ROS3D.makeColorMaterial(255, 0, 0, 1);
    var mesh = new ROS3D.MeshResource({
        path: repoPath,
        resource: filename,   // needs to be checked what type of geometry this is
        material: colorMaterial
    });
    updatePose(mesh, origin);
    return mesh;
}

function rpyToQuaternion(roll, pitch, yaw) {
    var phi = roll / 2.0;
    var the = pitch / 2.0;
    var psi = yaw / 2.0;
    var x = Math.sin(phi) * Math.cos(the) * Math.cos(psi) - Math.cos(phi) * Math.sin(the)
        * Math.sin(psi);
    var y = Math.cos(phi) * Math.sin(the) * Math.cos(psi) + Math.sin(phi) * Math.cos(the)
        * Math.sin(psi);
    var z = Math.cos(phi) * Math.cos(the) * Math.sin(psi) - Math.sin(phi) * Math.sin(the)
        * Math.cos(psi);
    var w = Math.cos(phi) * Math.cos(the) * Math.cos(psi) + Math.sin(phi) * Math.sin(the)
        * Math.sin(psi);

    quat = new ROSLIB.Quaternion({
        x: x,
        y: y,
        z: z,
        w: w
    });
    quat.normalize();
    return quat
}

function getThreePose(origin) {
    let x = origin.xyz[0];
    let y = origin.xyz[1];
    let z = origin.xyz[2];
    var pose = new ROSLIB.Pose({
        position: new ROSLIB.Vector3({
            x: origin.xyz[0],
            y: origin.xyz[1],
            z: origin.xyz[2]
        }),
        orientation: rpyToQuaternion(origin.rpy[0], origin.rpy[1], origin.rpy[2])
    });
    return pose;
}

function updatePose(obj, pose) {
    obj.position.set(pose.position.x, pose.position.y, pose.position.z);
    obj.quaternion.set(pose.orientation.x, pose.orientation.y,
        pose.orientation.z, pose.orientation.w);
    obj.updateMatrixWorld(true);
};

function getLink(links, linkName) {
    for (let i = 0; i < links.length; i++) {
        if (links[i].name == linkName) {
            return links[i]
        }
    }
    return undefined
}

function viewComponent(model, package_path) {
    let ws_path =  '/'

    let parent = undefined;
    let joint = model.joint[0]
    let parent_link_name = joint.parent.link
    let parent_link = getLink(model.link, parent_link_name)

    if (parent == undefined) {
        let axes = new ROS3D.Axes({});
        var origin = new ROSLIB.Pose({
            position: new ROSLIB.Vector3(0, 0, 0),
            orientation: new ROSLIB.Quaternion(0, 0, 0, 1)
        });
        updatePose(axes, origin);
        viewer.addObject(axes);
        parent = axes;    // TODO: this is mostly not right
    }

    if (parent_link !== undefined && parent_link.visual !== undefined) {
        var origin = new ROSLIB.Pose({
            position: new ROSLIB.Vector3(0, 0, 0),
            orientation: new ROSLIB.Quaternion(0, 0, 0, 1)
        });

        // remove 'package://', 'filepath://', etc
        meshPath = package_path + parent_link.visual.geometry.mesh.filename.replace('package://', '')
        parent = addMesh(meshPath, ws_path, origin);
        let axes = new ROS3D.Axes({});
        parent.add(axes);
        if (parent_link.visual.geometry.mesh.scale !== undefined) {
            parent.scale.set(...parent_link.visual.geometry.mesh.scale);
        }
        viewer.addObject(parent);
    }

    let joints = model.joint
    for (joint of joints) {
        let axes = new ROS3D.Axes({});
        childLink = getLink(model.link, joint.child.link)
        if (childLink.visual !== undefined) {
            meshPath = package_path + childLink.visual.geometry.mesh.filename.replace('package://', '')
            mesh = addMesh(meshPath, ws_path, getThreePose(joint.origin));
            mesh.add(axes);
            if (childLink.visual.geometry.mesh.scale !== undefined) {
                mesh.scale.set(...childLink.visual.geometry.mesh.scale);
            }
            parent.add(mesh);
            parent = mesh;
        } else {
            updatePose(axes, getThreePose(joint.origin));
            parent.add(axes);
            parent = axes;    // TODO: this is mostly not right
        }
    }

}
