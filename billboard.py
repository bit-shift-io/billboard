#!/usr/bin/env python

# https://superuser.com/questions/991371/ffmpeg-scale-and-pad#991412

# vlc image setting
# VLC menu: Tools > Preferences > ( Show settings = All ) > Input/Codecs \ Demuxers \ Image: Duration is seconds [10,00] < "Duration in seconds before simulating an end of file. A negative value means an unlimited play time."
# Do not forget to save changes and reastart VLC!

import os, sys,time, socket
import sys, getopt
import subprocess
import getpass

home = os.path.expanduser('~')

# variables
src_dir = os.path.join(str(home),'slides')
img_duration = 60 # seconds
stream_any='0.0.0.0'
stream_address='224.0.0.1'
stream_port=9999
log_level='quiet'


def get_slides():
    file_list = []
    for file in os.listdir(src_dir): #os.walk
        file_list.append(os.path.join(src_dir,file))
    return file_list


def convert_to_jpg():
    for f in get_slides():
        cmd = 'mogrify -format jpg ' + f
        subprocess.Popen( cmd, shell=True )


def launch_slideshow():
    print('launch slideshow')
    
    # calculate time
    frame_time = str(1.0 / img_duration)
    
    cmd = 'ffplay -fs -loop 0 -framerate '+frame_time+' -hide_banner -loglevel '+log_level+' -pattern_type glob -i "'+src_dir+'/*.jpg" -f image2 -vf "scale=w=1920:h=1080:force_original_aspect_ratio=1,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"'
    # play
    process = subprocess.Popen('exec ' + cmd,stdout=subprocess.PIPE,shell=True)
    return process
    #FILE_LIST=$(ls -d -1 $SRC_DIR/*.* | xargs) # all on single line
    #echo "images: $FILE_LIST"
    #check_call(vlc --playlist-autostart --loop --one-instance --fullscreen --no-video-title --no-qt-error-dialogs --quiet --no-playlist-tree --playlist-tree --image-duration $IMAGE_DURATION $SRC_DIR/*)


def launch_stream():
    print('launch stream')
    # cmd='ffplay -fs -noborder -hide_banner -i "'+src_dir+'/video.mp4" -vf "scale=-2:1080"'
    cmd='ffplay -fs -hide_banner -loglevel '+log_level+' -i "udp://'+stream_address+':'+str(stream_port)+'" -vf "scale=-2:1080"'
    #print (cmd)
    process = subprocess.Popen('exec ' + cmd,stdout=subprocess.PIPE,shell=True)
    return process
    #check_call(vlc --one-instance --one-instance --fullscreen --no-video-title --no-qt-error-dialogs --quiet --no-playlist-tree udp://@$MUTLICAST_ADDRESS:$MULTICAST_PORT)

    
def stream_exists():
    try:
        #stream_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        stream_socket=socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        # Allow multiple sockets to use the same PORT number
        stream_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        # Bind to the port that we know will receive multicast data
        stream_socket.bind((stream_any,stream_port))
        # Tell the kernel that we are a multicast socket
        stream_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        # Tell the kernel that we want to add ourselves to a multicast group
        # The address for the multicast group is the third param
        status = stream_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(stream_address) + socket.inet_aton(stream_any))
        # setblocking(0) is equiv to settimeout(0.0) which means we poll the socket.
        # But this will raise an error if recv() or send() can't immediately find or send data. 
        stream_socket.settimeout(0.5)   
        # see if we have data!
    except socket.error as e:
        print('plug in the network cable!')
 
    try:
        data, addr = stream_socket.recvfrom(1024)
    except socket.error as e:
        stream_socket.close()
        return False
    else:
        stream_socket.close()
        return True


def get_resolution():
    output = (subprocess.check_output('xrandr | grep "\*" | cut -d" " -f4',shell=True)).decode(encoding='UTF-8')

    displays = output.strip().splitlines()
    for display in displays:
        values = display.split('x')
        width = values[0]
        height = values[1]
        print ("Width:" + width + ",height:" + height)
        
        
def is_binary_installed(bin):
    try:
        output = (subprocess.check_output('which '+bin,shell=True)).decode(encoding='UTF-8')
    except subprocess.CalledProcessError as e:
        print ('Please install '+bin+' and try again!')   
    
    
def start():
    # time for os to load
    time.sleep(30)
    
    p_stream = None
    p_slideshow = None

    is_binary_installed('xrandr')
    is_binary_installed('ffplay')
    is_binary_installed('mogrify') 

    convert_to_jpg()
    slides = get_slides()
    
    get_resolution()
        
    # run slide show
    p_slideshow = launch_slideshow()

    # now we have a loop, if we detect a stream, run the stream
    while True:
        # sleepy time
        time.sleep(60)
  
        # check if stream exists
        s_exists = stream_exists()
        if s_exists and p_stream == None:
            p_slideshow.kill()
            p_slideshow = None
            p_stream = launch_stream()
        
        if not s_exists and p_stream != None and p_slideshow == None:
            p_stream.kill()
            p_stream = None
            slides = get_slides()
            p_slideshow = launch_slideshow()             
            
            
        # check if file list has changed if stream not active
        if p_stream == None and slides != get_slides():
            print('slides changed')
            convert_to_jpg()
            slides = get_slides()
            p_slideshow.kill()
            p_slideshow = launch_slideshow()            
  

def install_smb():
    smb_remote = input("Please enter network path(eg: //192.168.1.1/Documents/): ")
    smb_username = input("Please enter username: ")
    smb_password = input("Please enter password: ")
    
    # write to temp
    service_path = '/tmp/slides.mount'
    file = open(service_path,'w')
    file.write('[Unit]\n')
    file.write('  Description=cifs mount script\n')
    file.write('  Requires=network-online.target\n')
    file.write('  After=network-online.service\n')
    file.write('  Wants=network-online.target\n')
    file.write('\n')
    file.write('[Mount]\n')
    file.write('  What='+smb_remote+'\n')
    file.write('  Where='+src_dir+'\n')
    file.write('  Options=username='+smb_username+',password='+smb_password+',rw,x-systemd.automount\n')
    file.write('  Type=cifs\n')
    file.write('  TimeoutSec=10\n')
    file.write('\n')
    file.write('[Install]\n')
    file.write('  WantedBy=multi-user.target\n')
    file.close()
    
    # write to temp
    service_path = '/tmp/slides.automount'
    file = open(service_path,'w')
    file.write('[Unit]\n')
    file.write('  Description=cifs mount script\n')
    file.write('  Requires=network-online.target\n')
    file.write('  After=network-online.service\n')
    file.write('\n')
    file.write('[Automount]\n')
    file.write('  Where='+src_dir+'\n')
    file.write('  TimeoutIdleSec=10\n')
    file.write('\n')
    file.write('[Install]\n')
    file.write('  WantedBy=multi-user.target\n')
    file.close()
    
    # move with sudo
    service_path = '/etc/systemd/system/home-'+getpass.getuser()+'-slides.automount'
    os.system('sudo mv /tmp/slides.automount ' + service_path )
    
    service_path = '/etc/systemd/system/home-'+getpass.getuser()+'-slides.mount'
    os.system('sudo mv /tmp/slides.mount ' + service_path)
    
    cmd = 'systemctl enable home-'+getpass.getuser()+'-slides.mount'
    subprocess.Popen(cmd,shell=True)   
    
    cmd = 'systemctl enable home-'+getpass.getuser()+'-slides.automount'
    subprocess.Popen(cmd,shell=True)      
    
def install():
    service_path = home +'/.config/systemd/user/billboard.service'
    cmd = 'mkdir -p ' + home +'/.config/systemd/user/'
    subprocess.Popen(cmd,shell=True)
    
    py_path = os.path.realpath(__file__)
    file = open(service_path,'w')
    file.write('[Unit]\n')
    file.write('  Description=Slideshow Service\n')
    file.write('\n')
    file.write('[Service]\n')
    file.write('  Type=idle\n')
    file.write('  Environment=DISPLAY=:0\n')
    #file.write('  RemainAfterExit=true\n')
    file.write('  ExecStart=/usr/bin/python ' + py_path)
    file.write('\n\n')    
    file.write('[Install]\n')
    file.write('  WantedBy=default.target\n')
    file.write('\n')  
    file.close()
    
    cmd = 'loginctl enable-linger ' + getpass.getuser()
    subprocess.Popen(cmd,shell=True)
    
    cmd = 'systemctl --user enable billboard'
    subprocess.Popen(cmd,shell=True)

    
def remove():
    cmd = 'sudo systemctl disable billboard'
    process = subprocess.Popen(cmd,shell=True)
    
    cmd = 'systemctl disable home-'+getpass.getuser()+'-slides.mount'
    process = subprocess.Popen(cmd,shell=True)
    
    cmd = 'systemctl disable home-'+getpass.getuser()+'-slides.automount'
    process = subprocess.Popen(cmd,shell=True)
    
    cmd = 'sudo rm '+home+'/.config/systemd/user/billboard.service'
    process = subprocess.Popen(cmd,shell=True)
    
    cmd = 'sudo rm /etc/systemd/system/home-'+getpass.getuser()+'-slides.mount'
    process = subprocess.Popen(cmd,shell=True)
    
    cmd = 'sudo rm /etc/systemd/system/home-'+getpass.getuser()+'-slides.automount'
    process = subprocess.Popen(cmd,shell=True)   
    
###################################
def main(argv):
    try:
        opts, args = getopt.getopt(argv,"hirs",[""])
    except getopt.GetoptError:
        print ('Invalid arguments use -h to show help')
        sys.exit(2)
        
    for opt, arg in opts:
        if opt == '-h':
            print ('tool-slideshow.py -i   to install as system service')
            print ('tool-slideshow.py -r   to remove as system service')
            print ('tool-slideshow.py -s   to configure samba mount')
            sys.exit()
        elif opt in ("-i", "--install"):
            install()
            sys.exit()
        elif opt in ("-r", ""):      
            remove()
            sys.exit()
        elif opt in ("-s", ""):   
            install_smb()
            sys.exit() 
            
    start()
    

###################################
if __name__ == "__main__":
   main(sys.argv[1:])
