# hadolint global ignore=DL3003

FROM quay.io/pypa/manylinux2014_x86_64:2024-04-23-ef7507e

ADD https://downloads.xiph.org/releases/ogg/libogg-1.3.5.tar.xz \
    https://downloads.xiph.org/releases/vorbis/libvorbis-1.3.7.tar.xz \
    https://downloads.xiph.org/releases/flac/flac-1.4.3.tar.xz \
    https://downloads.xiph.org/releases/opus/opus-1.4.tar.gz \
    https://github.com/libsndfile/libsndfile/releases/download/1.2.2/libsndfile-1.2.2.tar.xz /tmp/

WORKDIR /tmp/

COPY ./utils/SHA256SUMS.txt .

RUN sha256sum -c SHA256SUMS.txt

RUN tar xf libogg-1.3.5.tar.xz && cd libogg-1.3.5 && \
    ./configure --prefix=/usr --libdir=/usr/lib64 && \
    make -j "$(nproc --all)" && make install && ldconfig && \
    rm -rf /usr/share/doc/libogg && rm -rf /tmp/libogg-1.3.5*

RUN tar xf libvorbis-1.3.7.tar.xz && cd libvorbis-1.3.7 && \
    ./configure --prefix=/usr --libdir=/usr/lib64 && \
    make -j "$(nproc --all)" && make install && ldconfig && \
    rm -rf /usr/share/doc/libvorbis-1.3.7 && rm -rf /tmp/libvorbis-1.3.7*

RUN tar xf flac-1.4.3.tar.xz && cd flac-1.4.3 && \
    ./configure --prefix=/usr --libdir=/usr/lib64 --disable-cpplibs --disable-programs && \
    make -j "$(nproc --all)" && make install && ldconfig && \
    rm -rf /usr/share/doc/flac && rm /usr/share/man/man1/*flac.1 && rm -rf /tmp/flac-1.4.3*

RUN tar xf opus-1.4.tar.gz && cd opus-1.4 && \
    ./configure --prefix=/usr --libdir=/usr/lib64 --disable-static --disable-doc --disable-extra-programs && \
    make -j "$(nproc --all)" && make install && ldconfig && \
    rm -rf /tmp/opus-1.4*

RUN tar xf libsndfile-1.2.2.tar.xz && cd libsndfile-1.2.2 && \
    ./configure --prefix=/usr --libdir=/usr/lib64 --disable-full-suite --disable-mpeg && \
    make -j "$(nproc --all)" && make install && ldconfig && \
    rm -rf /tmp/libsndfile-1.2.2*

WORKDIR /

# Remove unsupported Python version:
RUN rm -v /opt/python/cp36-cp36m

COPY ./utils/pip.conf /etc/

COPY ./utils/build-wheels.sh /

CMD ["/build-wheels.sh"]
