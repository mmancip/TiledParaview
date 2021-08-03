FROM mageianvidia

MAINTAINER  "Martial Mancip" <Martial.Mancip@MaisondelaSimulation.fr>

RUN urpmi.addmedia updates http://ftp.free.fr/mirrors/mageia.org/distrib/7/x86_64/media/core/updates && \
    urpmi.addmedia release http://ftp.free.fr/mirrors/mageia.org/distrib/7/x86_64/media/core/release && \
    urpmi.removemedia "Core Updates" && \
    urpmi.removemedia "Core Release" && \
    urpmi.update -a

RUN dnf install -y paraview
#RUN dnf install -y lib64Qt5Core
RUN strip --remove-section=.note.ABI-tag /usr/lib64/libQt5Core.so.5.12.6
RUN dnf install -y openmpi

