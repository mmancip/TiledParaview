#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import sys,os,time
import code
import argparse
import re, datetime
import inspect

# sys.path.append(os.path.realpath('/TiledViz/TVConnections/'))
# from connect import sock

import json

if (os.path.exists("config.tar")):
    os.system("tar xf config.tar")

SITE_config='./site_config.ini'
CASE_config="./case_config.ini"

actions_file=open("/home/myuser/actions.json",'r')
tiles_actions=json.load(actions_file)
#launch_actions()

config = configparser.ConfigParser()
config.optionxform = str

config.read(SITE_config)

TILEDOCKERS_path=config['SITE']['TILEDOCKER_DIR']
DOCKERSPACE_DIR=config['SITE']['DOCKERSPACE_DIR']
#NOVNC_URL=config['SITE']['NOVNC_URL']
GPU_FILE=config['SITE']['GPU_FILE']

HTTP_FRONTEND=config['SITE']['HTTP_FRONTEND']
HTTP_LOGIN=config['SITE']['HTTP_LOGIN']
HTTP_IP=config['SITE']['HTTP_IP']
init_IP=config['SITE']['init_IP']

config.read(CASE_config)

CASE_DOCKER_PATH=config['CASE']['CASE_DOCKER_PATH']
NUM_DOCKERS=int(config['CASE']['NUM_DOCKERS'])

network=config['CASE']['network']
nethost=config['CASE']['nethost']
domain=config['CASE']['domain']

OPTIONssh=config['CASE']['OPTIONssh']
SOCKETdomain=config['CASE']['SOCKETdomain']

DOCKER_NAME=config['CASE']['DOCKER_NAME']

DATA_PATH=config['CASE']['DATA_PATH']
DATA_MOUNT_DOCKER=config['CASE']['DATA_MOUNT_DOCKER']
DATA_PATH_DOCKER=config['CASE']['DATA_PATH_DOCKER']

OPTIONS=config['CASE']['OPTIONS'].replace("$","").replace('"','')
print("\nOPTIONS from CASE_CONFIG : "+OPTIONS)
def replaceconf(x):
    if (re.search('}',x)):
        varname=x.replace("{","").replace("}","")
        return config['CASE'][varname]
    else:
        return x
OPTIONS=OPTIONS.replace("JOBPath",JOBPath)
OPTIONS=OPTIONS.replace('{','|{').replace('}','}|').split('|')
#print("OPTIONS before replacement : "+str(OPTIONS))

OPTIONS="".join(list(map( replaceconf,OPTIONS)))
print("OPTIONS after replacement : "+OPTIONS)


CreateTS='create TS='+TileSet+' Nb='+str(NUM_DOCKERS)

client.send_server(CreateTS)

# get TiledParaview package from Github
COMMAND_GIT="git clone https://github.com/mmancip/TiledParaview.git"
print("command_git : "+COMMAND_GIT)
os.system(COMMAND_GIT)

# Global commands
# Execute on each/a set of tiles
ExecuteTS='execute TS='+TileSet+" "
# Launch a command on the frontend
LaunchTS='launch TS='+TileSet+" "+JOBPath+' '

# Send CASE and SITE files
try:
    client.send_server(LaunchTS+' chmod og-rxw '+JOBPath)
    print("Out of chmod JOBPath : "+ str(client.get_OK()))

    send_file_server(client,TileSet,".", CASE_config, JOBPath)
    CASE_config=os.path.join(JOBPath,CASE_config)
    send_file_server(client,TileSet,".", SITE_config, JOBPath)
    SITE_config=os.path.join(JOBPath,os.path.basename(SITE_config))
    send_file_server(client,TileSet,".", "tagliste", JOBPath)
    send_file_server(client,TileSet,".", "list_hostsgpu", JOBPath)

except:
    print("Error sending files !")
    traceback.print_exc(file=sys.stdout)
    try:
        code.interact(banner="Try sending files by yourself :",local=dict(globals(), **locals()))
    except SystemExit:
        pass



COMMAND_TiledParaview=LaunchTS+COMMAND_GIT
client.send_server(COMMAND_TiledParaview)
print("Out of git clone TiledParaview : "+ str(client.get_OK()))

COMMAND_copy=LaunchTS+" cp -rp TiledParaview/paraview_client "+\
               "TiledParaview/build_nodes_file "+\
               "./"

client.send_server(COMMAND_copy)
print("Out of copy scripts from TiledCourse : "+ str(client.get_OK()))

# Launch containers HERE
REF_CAS=str(NUM_DOCKERS)+" "+DATE+" "+DOCKERSPACE_DIR+" "+DOCKER_NAME

print("\nREF_CAS : "+REF_CAS)

COMMANDStop=os.path.join(TILEDOCKERS_path,"stop_dockers")+" "+REF_CAS+" "+os.path.join(JOBPath,GPU_FILE)
print("\n"+COMMANDStop)
sys.stdout.flush()

# Launch dockers
stateVM=True
def Run_dockers():
    global stateVM
    COMMAND="bash -c \""+os.path.join(TILEDOCKERS_path,"launch_dockers")+" "+REF_CAS+" "+GPU_FILE+" "+HTTP_FRONTEND+":"+HTTP_IP+\
            " "+network+" "+nethost+" "+domain+" "+init_IP+" TileSetPort "+UserFront+"@"+Frontend+" "+OPTIONS+\
            " > "+os.path.join(JOBPath,"output_launch")+" 2>&1 \"" 

    print("\nCommand dockers : "+COMMAND)

    client.send_server(LaunchTS+' '+COMMAND)
    state=client.get_OK()
    stateVM=stateVM and (state == 0)
    print("Out of launch docker : "+ str(state))
    sys.stdout.flush()

Run_dockers()
sys.stdout.flush()

taglist = open("tagliste", "r")
# TODO : give a liste of lines !
# tab=taglist.readlines()
# line=tab[123]
# file_name=(line[1].split('='))[1].replace('"','')


# Build nodes.json file from new dockers list
def build_nodes_file():
    global stateVM
    print("Build nodes.json file from new dockers list.")
    # COMMAND=LaunchTS+' chmod u+x build_nodes_file '
    # client.send_server(COMMAND)
    # print("Out of chmod build_nodes_file : "+ str(client.get_OK()))

    COMMAND=LaunchTS+' ./build_nodes_file '+os.path.join(JOBPath,CASE_config)+' '+os.path.join(JOBPath,SITE_config)+' '+TileSet
    print("\nCommand dockers : "+COMMAND)

    client.send_server(COMMAND)
    state=client.get_OK()
    stateVM=stateVM and (state == 0)
    print("Out of build_nodes_file : "+ str(state))
    time.sleep(2)

if (stateVM):
    build_nodes_file()
sys.stdout.flush()

time.sleep(2)
# Launch docker tools
def launch_resize(RESOL="1440x900"):
    client.send_server(ExecuteTS+' xrandr --fb '+RESOL)
    state=client.get_OK()
    print("Out of xrandr : "+ str(state))

if (stateVM):
    launch_resize()
sys.stdout.flush()

def launch_tunnel():
    global stateVM
    # Call tunnel for VNC
    client.send_server(ExecuteTS+' /opt/tunnel_ssh '+HTTP_FRONTEND+' '+HTTP_LOGIN)
    state=client.get_OK()
    stateVM=stateVM and (state == 0)
    print("Out of tunnel_ssh : "+ str(state))
    if (not stateVM):
        return

    # Get back PORT
    for i in range(NUM_DOCKERS):
        i0="%0.3d" % (i+1)
        client.send_server(ExecuteTS+' Tiles=('+containerId(i+1)+') '+
                           'bash -c "cat .vnc/port |xargs -I @ sed -e \"s#port='+SOCKETdomain+i0+'#port=@#\" -i CASE/nodes.json"')
        state=client.get_OK()
        stateVM=stateVM and (state == 0)
        print("Out of change port %s : " % (i0) + str(state))
    if (not stateVM):
        return

    sys.stdout.flush()
    if (not stateVM):
        return
    launch_nodes_json()

if (stateVM):
    launch_tunnel()
sys.stdout.flush()

def launch_vnc():
    global stateVM
    client.send_server(ExecuteTS+' /opt/vnccommand')
    state=client.get_OK()
    stateVM=stateVM and (state == 0)
    print("Out of vnccommand : "+ str(state))

if (stateVM):
    launch_vnc()
sys.stdout.flush()


def launch_one_client(script='paraview_client',tileNum=-1,tileId='001'):
    line=taglist.readline().split(' ')
    dir_name=(line[2].split('='))[1].replace('"','')
    COMMAND=' '+os.path.join(CASE_DOCKER_PATH,script)+' '+DATA_PATH_DOCKER+' '+dir_name
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '
    else:
        TilesStr=' Tiles=('+tileId+') '
    print("launch command on %s : %s" % (TilesStr,COMMAND))
    CommandTS=ExecuteTS+TilesStr+COMMAND
    client.send_server(CommandTS)        
    client.get_OK()

# TODO : give a list of lines !
def Run_clients():
    for i in range(NUM_DOCKERS):
        launch_one_client(tileNum=i)
    Last_Elt=NUM_DOCKERS-1

if (stateVM):
    Run_clients()
sys.stdout.flush()

def next_element(script='paraview_client',tileNum=-1,tileId='001'):
    line2=taglist.readline()
    line=line2.split(' ')
    dir_name=(line[2].split('='))[1].replace('"','')
    COMMAND=' '+os.path.join(CASE_DOCKER_PATH,script)+' '+DATA_PATH_DOCKER+' '+dir_name
    COMMANDKill=' killall -9 paraview'
    if ( tileNum > -1 ):
        tileId=containerId(tileNum+1)
    else:
        tileNum=int(tileId)-1 
    TilesStr=' Tiles=('+tileId+') '
    print("%s Client command : %s" % (TilesStr,COMMAND))

    CommandTSK=ExecuteTS+TilesStr+COMMANDKill
    client.send_server(CommandTSK)
    client.get_OK()
    
    CommandTS=ExecuteTS+TilesStr+COMMAND
    client.send_server(CommandTS)
    client.get_OK()

    nodesf=open("nodes.json",'r')
    nodes=json.load(nodesf)
    nodesf.close()

    nodes["nodes"][tileNum]["title"]=tileId+" "+dir_name
    if ("variable" in nodes["nodes"][tileNum]):
        nodes["nodes"][tileNum]["variable"]="ID-"+tileId+"_"+dir_name
    nodes["nodes"][tileNum]["comment"]=line2
    if ("usersNotes" in nodes["nodes"][tileNum]):
        nodes["nodes"][tileNum]["usersNotes"]=re.sub(r'dir .*',"dir "+dir_name,
                                                     nodes["nodes"][tileNum]["usersNotes"])
    nodes["nodes"][tileNum]["tags"]=[]
    nodes["nodes"][tileNum]["tags"].append(TileSet)
    nodes["nodes"][tileNum]["tags"].append("NewElement")

    nodesf=open("nodes.json",'w')
    nodesf.write(json.dumps(nodes))
    nodesf.close()
    
    
def remove_element(script='paraview_client',tileNum=-1,tileId='001'):
    COMMANDKill=' killall -9 Xvnc'
    if ( tileNum > -1 ):
        tileId=containerId(tileNum+1)
    else:
        tileNum=int(tileId)-1 
    TilesStr=' Tiles=('+tileId+') '
    print("%s VMD command : %s" % (TilesStr,COMMANDKill))

    CommandTSK=ExecuteTS+TilesStr+COMMANDKill
    client.send_server(CommandTSK)
    client.get_OK()

    nodesf=open("nodes.json",'r')
    nodes=json.load(nodesf)
    nodesf.close()

    del nodes["nodes"][tileNum]
    
    nodesf=open("nodes.json",'w')
    nodesf.write(json.dumps(nodes))
    nodesf.close()
        

def init_wmctrl():
    client.send_server(ExecuteTS+' wmctrl -l -G')
    print("Out of wmctrl : "+ str(client.get_OK()))

if (stateVM):
    init_wmctrl()

def launch_changesize(RESOL="1920x1080",tileNum=-1,tileId='001'):
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '
    else:
        TilesStr=' Tiles=('+tileId+') '
    COMMAND=ExecuteTS+TilesStr+' xrandr --fb '+RESOL
    print("call server with : "+COMMAND)
    client.send_server(COMMAND)
    print("server answer is "+str(client.get_OK()))

def launch_smallsize(tileNum=-1,tileId='001'):
    print("Launch launch_changesize smallsize for tile "+str(tileNum))
    launch_changesize(tileNum=tileNum,RESOL="950x420")

def launch_bigsize(tileNum=-1,tileId='001'):
    print("Launch launch_changesize bigsize for tile "+str(tileNum))
    launch_changesize(tileNum=tileNum,RESOL="1920x1200")

def get_windows():
    client.send_server(ExecuteTS+' wmctrl -l -G')
    print("Out of wmctrl : "+ str(client.get_OK()))
get_windows()

def fullscreenApp(windowname="paraview",tileNum=-1):
    fullscreenThisApp(App=windowname,tileNum=tileNum)

def movewindows(windowname="paraview",wmctrl_option='toggle,fullscreen',tileNum=-1,tileId='001'):
    #remove,maximized_vert,maximized_horz
    #toggle,above
    #movewindows(windowname='paraview',wmctrl_option="toggle,fullscreen",tileNum=2)
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '
    else:
        TilesStr=' Tiles=('+tileId+') '
    client.send_server(ExecuteTS+TilesStr+'/opt/movewindows '+windowname+' -b '+wmctrl_option)
    client.get_OK()

def toggle_fullscr():
    for i in range(NUM_DOCKERS):
        client.send_server(ExecuteTS+' Tiles=('+containerId(i+1)+') '+
                           '/opt/movewindows OpenGL -b toggle,fullscreen')
        client.get_OK()

def kill_all_containers():
    client.send_server(ExecuteTS+' killall Xvnc')
    print("Out of killall command : "+ str(client.get_OK()))
    client.send_server(LaunchTS+" "+COMMANDStop)
    client.close()

launch_actions_and_interact()

kill_all_containers()

sys.exit(0)


