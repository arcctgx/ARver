#!/bin/bash -e

# Copy AccurateRip dBAR file to Whipper cache.
#
# Whipper accurip cache directory structure:
#
# x/
#   y/
#     z/
#       dBAR-HHH-HHHHHzyx-HHHHHHHH-HHHHHHHH.bin
#
# "dBAR" is constant literal. H, x, y and z are hex digits.
#
# Example: file dBAR-016-00283af3-01f86e5a-d5116e10.bin
# is placed in cache subdirectory 3/f/a/.
#
# TODO Check if arguments match dBAR file name template.
# TODO Accept multiple files.

get_cache_dir() {
    local -r name="$(basename "${1}")"
    local -r z="$(cut -c15 <<< "${name}")"
    local -r y="$(cut -c16 <<< "${name}")"
    local -r x="$(cut -c17 <<< "${name}")"

    local -r whipper_cache="${HOME}/.cache/whipper/accurip"
    local -r cache_dir="${whipper_cache}/${x}/${y}/${z}"

    echo "${cache_dir}"
}

main() {
    if [[ $# -ne 1 ]]; then
        echo "usage: $(basename "$0") <dBAR-file>"
        exit 1
    fi

    cache_dir=$(get_cache_dir "${1}")
    mkdir -pv "${cache_dir}"
    cp -va "${1}" "${cache_dir}"
}

main "${@}"
