# kinematic_components_web_app
##Setup:
1. fork the kinematic_components_web_app to your github repo
2. create an ssh key for the secured connection to your repo using command "ssh-keygen"
3. add ssh key to your github 
4. create a workspace directory in your root directory
5. create a virtual python environment using the command: python3 -m venv3
6. then activate using command: source venv3/bin/activate
7. Now clone the github repo using the ssh key
8. run the requirements.txt file for installing necessary packages using the command: pip install -r requirements.txt
9. Install ament_index_python by using the command: sudo apt install ament_index_python
10. If the above command gives error install aptitude using: sudo apt install aptitude, then use: sudo aptitude install ament_index_python
11. for other requirements to work, use the following commands in the same order:
locale  # check for UTF-8

sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

locale  # verify settings

sudo apt install software-properties-common
sudo add-apt-repository universe

sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt upgrade
sudo apt install ros-humble-desktop

12. After installing all the required packages, run: python app.py
