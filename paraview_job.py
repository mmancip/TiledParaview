#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import sys,os,time
import code
import argparse
import re, datetime
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
def Run_dockers():
    COMMAND="bash -c \""+os.path.join(TILEDOCKERS_path,"launch_dockers")+" "+REF_CAS+" "+GPU_FILE+" "+HTTP_FRONTEND+":"+HTTP_IP+\
            " "+network+" "+nethost+" "+domain+" "+init_IP+" TileSetPort "+UserFront+"@"+Frontend+" "+OPTIONS+\
            " > "+os.path.join(JOBPath,"output_launch")+" 2>&1 \"" 

    print("\nCommand dockers : "+COMMAND)

    client.send_server(LaunchTS+' '+COMMAND)
    print("Out of launch dockers : "+ str(client.get_OK()))
    sys.stdout.flush()

Run_dockers()
sys.stdout.flush()

# Build nodes.json file from new dockers list
def build_nodes_file():
    print("Build nodes.json file from new dockers list.")
    # COMMAND=LaunchTS+' chmod u+x build_nodes_file '
    # client.send_server(COMMAND)
    # print("Out of chmod build_nodes_file : "+ str(client.get_OK()))

    COMMAND=LaunchTS+' ./build_nodes_file '+os.path.join(JOBPath,CASE_config)+' '+os.path.join(JOBPath,SITE_config)+' '+TileSet
    print("\nCommand dockers : "+COMMAND)

    client.send_server(COMMAND)
    print("Out of build_nodes_file : "+ str(client.get_OK()))
    time.sleep(2)

build_nodes_file()
sys.stdout.flush()

time.sleep(2)
# Launch docker tools
def launch_resize(RESOL="1440x900"):
    client.send_server(ExecuteTS+' xrandr --fb '+RESOL)
    print("Out of xrandr : "+ str(client.get_OK()))

launch_resize()
sys.stdout.flush()

def launch_tunnel():
    # Call tunnel for VNC
    client.send_server(ExecuteTS+' /opt/tunnel_ssh '+HTTP_FRONTEND+' '+HTTP_LOGIN)
    print("Out of tunnel_ssh : "+ str(client.get_OK()))
    # Get back PORT
    for i in range(NUM_DOCKERS):
        i0="%0.3d" % (i+1)
        client.send_server(ExecuteTS+' Tiles=('+containerId(i+1)+') '+
                           'bash -c "cat .vnc/port |xargs -I @ sed -e \"s#port='+SOCKETdomain+i0+'#port=@#\" -i CASE/nodes.json"')
        print("Out of change port %s : " % (i0) + str(client.get_OK()))

    sys.stdout.flush()
    launch_nodes_json()

launch_tunnel()
sys.stdout.flush()

def launch_vnc():
    client.send_server(ExecuteTS+' /opt/vnccommand')
    print("Out of vnccommand : "+ str(client.get_OK()))

launch_vnc()
sys.stdout.flush()


def launch_one_client(script='paraview_client',tileNum=-1,tileId='001'):
    COMMAND=' '+os.path.join(CASE_DOCKER_PATH,script)
    if ( tileNum > -1 ):
        TilesStr=' Tiles=('+containerId(tileNum+1)+') '
    else:
        TilesStr=' Tiles=('+tileId+') '
    print("launch command on %s : %s" % (TilesStr,COMMAND))
    CommandTS=ExecuteTS+TilesStr+COMMAND
    client.send_server(CommandTS)        
    client.get_OK()

def launch_client_global(script='paraview_client'):
    COMMAND=' '+os.path.join(CASE_DOCKER_PATH,script)
    print("launch command on all tiles : %s" % (COMMAND))
    sys.stdout.flush()
    CommandTS=ExecuteTS+COMMAND
    client.send_server(CommandTS)

    client.get_OK()

launch_client_global(script='paraview_client')

def next_element(script='paraview_client',tileNum=-1,tileId='001'):
    COMMAND=' '+os.path.join(CASE_DOCKER_PATH,script)
    COMMANDKill=' killall -9 glxgears'
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

    import socket
    hostname=socket.gethostname()

    nodes["nodes"][tileNum]["title"]=tileId+" "+hostname
    if ("variable" in nodes["nodes"][tileNum]):
        nodes["nodes"][tileNum]["variable"]="ID-"+tileId+"_"+hostname
    nodes["nodes"][tileNum]["comment"]="New comment for tile "+tileId
    # if ("usersNotes" in nodes["nodes"][tileNum]):
    #     nodes["nodes"][tileNum]["usersNotes"]=re.sub(r'file .*',"New Element host "+hostname,
    #                                                  nodes["nodes"][tileNum]["usersNotes"])
    nodes["nodes"][tileNum]["usersNotes"]="New Element host "+hostname
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

def fullscreenApp(windowname="glxgears",tileNum=-1):
    fullscreenThisApp(App=windowname,tileNum=tileNum)

def movewindows(windowname="glxgears",wmctrl_option='toggle,fullscreen',tileNum=-1,tileId='001'):
    #remove,maximized_vert,maximized_horz
    #toggle,above
    #movewindows(windowname='glxgears',wmctrl_option="toggle,fullscreen",tileNum=2)
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

