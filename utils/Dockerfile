FROM quay.io/pypa/manylinux2014_x86_64

WORKDIR /tmp/

ADD https://downloads.xiph.org/releases/flac/flac-1.4.3.tar.xz .
ADD https://downloads.xiph.org/releases/opus/opus-1.4.tar.gz .
ADD https://github.com/libsndfile/libsndfile/releases/download/1.2.2/libsndfile-1.2.2.tar.xz .

RUN yum install -y libvorbis-devel && yum clean all

RUN tar xf flac-1.4.3.tar.xz && cd flac-1.4.3 && \
    ./configure --prefix=/usr --libdir=/usr/lib64 --disable-cpplibs --disable-programs && \
    make -j $(nproc --all) && make install && ldconfig && \
    rm -rf /usr/share/doc/flac && rm -rf /tmp/flac-1.4.3*

RUN tar xf opus-1.4.tar.gz && cd opus-1.4 && \
    ./configure --prefix=/usr --libdir=/usr/lib64 --disable-static --disable-doc --disable-extra-programs && \
    make -j $(nproc --all) && make install && ldconfig && \
    rm -rf /tmp/opus-1.4*

RUN tar xf libsndfile-1.2.2.tar.xz && cd libsndfile-1.2.2 && \
    ./configure --prefix=/usr --libdir=/usr/lib64 --disable-full-suite && \
    make -j $(nproc --all) && make install && ldconfig && \
    rm -rf /tmp/libsndfile-1.2.2*

WORKDIR /
