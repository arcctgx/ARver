#!/bin/bash -eux

# Script for building manylinux wheels. Adapted from pypa/python-manylinux-demo.
# This script is the entry point of arcctgx/arver-builder container. It expects
# package sources to be available in /package directory inside the container.
# This can be achieved with Docker bind mount, e.g.:
#
# docker run --rm -u 1000:100 -v "$(pwd):/package" arcctgx/arver-builder
#

platform="manylinux2014_x86_64"
package_dir="/package"
wheel_dir="${package_dir}/wheelhouse"

if [[ ! -d "${package_dir}" ]]; then
    echo "The directory ${package_dir} is not available inside container."
    exit 1
fi

# start with clean state:
rm -rf "${package_dir}/build" "${wheel_dir}"

# build wheels for all Python interpreters installed in the container:
find /opt/python/ -type l | sort -V |
while read -r pyint
do
    pybin="${pyint}/bin"
    "${pybin}/pip" wheel "${package_dir}" --wheel-dir "${wheel_dir}"
done

# vendor required shared libraries in wheels:
find "${wheel_dir}" -type f -name "*.whl" | sort -V |
while read -r wheel
do
    if ! auditwheel show "${wheel}"; then
        echo "Skipping non-platform wheel ${wheel}"
        continue
    fi

    auditwheel repair "${wheel}" --plat "${platform}" --strip --wheel-dir "${wheel_dir}"
done
