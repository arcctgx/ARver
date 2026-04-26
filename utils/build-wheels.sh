#!/bin/bash -eux

# Script for building manylinux wheels. Adapted from pypa/python-manylinux-demo.
# This script is executed in one of the PyPA manylinux containers. It assumes
# package sources are available in /pkg directory inside the container.
#
# Usage examples:
#
# docker run --rm -e PLAT=manylinux2014_x86_64 -v $(pwd -P):/pkg quay.io/pypa/manylinux2014_x86_64 /pkg/utils/build-wheels.sh
# docker run --rm -e PLAT=manylinux2014_i686 -v $(pwd -P):/pkg quay.io/pypa/manylinux2014_i686 linux32 /pkg/utils/build-wheels.sh
# docker run --rm -e PLAT=musllinux_1_2_x86_64 -v $(pwd -P):/pkg quay.io/pypa/musllinux_1_2_x86_64 /pkg/utils/build-wheels.sh
# docker run --rm -e PLAT=musllinux_1_2_i686 -v $(pwd -P):/pkg quay.io/pypa/musllinux_1_2_i686 /pkg/utils/build-wheels-new.sh

package_dir="/pkg"
dist_dir="${package_dir}/dist"
wheel_dir="${package_dir}/wheelhouse"

if [[ ! -d "${package_dir}" ]]; then
    echo "The directory ${package_dir} is not available inside container."
    exit 1
fi

# start with clean state:
rm -rfv "${dist_dir}"

# build and install libsndfile with its dependencies:
pushd /tmp

curl -O -L https://downloads.xiph.org/releases/ogg/libogg-1.3.5.tar.xz
curl -O -L https://downloads.xiph.org/releases/vorbis/libvorbis-1.3.7.tar.xz
curl -O -L https://downloads.xiph.org/releases/flac/flac-1.4.3.tar.xz
curl -O -L https://downloads.xiph.org/releases/opus/opus-1.4.tar.gz
curl -O -L https://github.com/libsndfile/libsndfile/releases/download/1.2.2/libsndfile-1.2.2.tar.xz
sha256sum -c "${package_dir}/utils/SHA256SUMS.txt"

tar xf libogg-1.3.5.tar.xz
pushd libogg-1.3.5
./configure
make -j "$(nproc --all)"
make install
ldd --version |& grep -q "musl libc" || ldconfig
popd

tar xf libvorbis-1.3.7.tar.xz
pushd libvorbis-1.3.7
./configure
make -j "$(nproc --all)"
make install
ldd --version |& grep -q "musl libc" || ldconfig
popd

tar xf flac-1.4.3.tar.xz
pushd flac-1.4.3
./configure --disable-cpplibs --disable-programs
make -j "$(nproc --all)"
make install
ldd --version |& grep -q "musl libc" || ldconfig
popd

tar xf opus-1.4.tar.gz
pushd opus-1.4
./configure --disable-static --disable-doc --disable-extra-programs
make -j "$(nproc --all)"
make install
ldd --version |& grep -q "musl libc" || ldconfig
popd

tar xf libsndfile-1.2.2.tar.xz
pushd libsndfile-1.2.2
./configure --disable-full-suite --disable-mpeg
make -j "$(nproc --all)"
make install
ldd --version |& grep -q "musl libc" || ldconfig
popd

popd

# Py_LIMITED_API 0x03070000 is defined, so it's sufficient to build
# just one wheel with any Python version:
python3.8 -m build "${package_dir}"

# vendor required shared libraries in wheels:
for wheel in "${dist_dir}"/*.whl
do
    if ! auditwheel show "${wheel}"; then
        echo "Skipping non-platform wheel ${wheel}"
        continue
    fi

    auditwheel repair "${wheel}" --plat "${PLAT}" --strip --wheel-dir "${wheel_dir}"
    rm -v "${wheel}"
done
