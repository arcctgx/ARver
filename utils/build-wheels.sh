#!/bin/bash -eux

# Script for building manylinux wheels. Adapted from pypa/python-manylinux-demo.
# This script is intended to be executed inside manylinux container, e.g.:
#
# docker run --rm -v "$(pwd)":/package \
#   quay.io/pypa/manylinux2014_x86_64 \
#   /package/utils/build-wheels.sh
#

platform="manylinux2014_x86_64"
package_dir="/package"
wheel_dir="${package_dir}/wheelhouse"

# start with clean state:
rm -rf "${package_dir}/build" "${wheel_dir}"

# ARver requires Python >= 3.7, so remove Python-3.6 symlink:
rm -rf /opt/python/cp36-cp36m

# install system packages required to build C extensions:
yum install -y libsndfile-devel

# build CPython wheels:
for pybin in /opt/python/cp*/bin
do
    "${pybin}/pip" wheel "${package_dir}" --no-deps --wheel-dir "${wheel_dir}"
done

# vendor required shared libraries in wheels:
for wheel in "${wheel_dir}"/*.whl
do
    if ! auditwheel show "${wheel}"; then
        echo "Skipping non-platform wheel ${wheel}"
        continue
    fi

    auditwheel repair "${wheel}" --plat "${platform}" --wheel-dir "${wheel_dir}"
done
