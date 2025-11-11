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
dist_dir="${package_dir}/dist"

if [[ ! -d "${package_dir}" ]]; then
    echo "The directory ${package_dir} is not available inside container."
    exit 1
fi

# start with clean state:
rm -rf "${package_dir}/build" "${dist_dir}/*"

# Py_LIMITED_API 0x03070000 is defined, so it's sufficient to build
# just one wheel with any Python version:
python3.8 -m build "${package_dir}" --outdir "${dist_dir}"

# vendor required shared libraries in wheels:
for wheel in "${dist_dir}"/*.whl
do
    if ! auditwheel show "${wheel}"; then
        echo "Skipping non-platform wheel ${wheel}"
        continue
    fi

    auditwheel repair "${wheel}" --plat "${platform}" --strip --wheel-dir "${dist_dir}"
    rm -v "${wheel}"
done
