_arver_completion() {
    local cur prev opts files devices
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts="-1 --use-arv1 -d --drive -D --data-length -i --disc-id \
          -p --permissive -P --pregap-length -t --track-lengths \
          -v --version -x --exclude"

    if [[ ${cur} == -* ]]; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    case "${prev}" in
        -d|--drive)
            devices=$(compgen -G "/dev/cd*"; compgen -G "/dev/dvd*"; compgen -G "/dev/sr*")
            COMPREPLY=( $(compgen -W "${devices}" -- ${cur}) )
            return 0
            ;;
        -x|--exclude)
            shopt -s nocaseglob
            files=$(compgen -G "*.wav"; compgen -G "*.flac" -- ${cur})
            shopt -u nocaseglob
            COMPREPLY=( ${files} )
            return 0
            ;;
    esac

    shopt -s nocaseglob
    files=$(compgen -G "*.wav"; compgen -G "*.flac" -- ${cur})
    shopt -u nocaseglob
    COMPREPLY=( ${files} )
}

complete -F _arver_completion arver
