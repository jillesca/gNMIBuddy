#!/usr/bin/env bash

# Bash completion for gNMIBuddy CLI
# Save this file as gnmibuddy-completion.bash and source it in your shell

_gnmibuddy_completions() {
    local cur prev opts commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Main CLI options
    local main_opts="--help -h --version -V --version-detailed --log-level --module-log-levels --structured-logging --quiet-external --all-devices --max-workers --inventory"

    # Main command groups and aliases
    local groups="device d network n topology t ops o manage m"

    # Device group commands
    local device_commands="info profile list"

    # Network group commands  
    local network_commands="routing interface mpls vpn"

    # Topology group commands
    local topology_commands="adjacency neighbors"

    # Ops group commands
    local ops_commands="logs test-all"

    # Manage group commands
    local manage_commands="list-commands log-level"

    # Output format options
    local output_formats="json yaml table"

    # Log level options
    local log_levels="debug info warning error"

    # Function to complete device names from inventory
    _complete_devices() {
        local devices=""
        # Try to get device list from inventory if available
        if command -v gnmibuddy &> /dev/null; then
            devices=$(gnmibuddy device list 2>/dev/null | grep -v "^Device" | grep -v "^-" | awk '{print $1}' | tr '\n' ' ')
        fi
        COMPREPLY=($(compgen -W "${devices}" -- "${cur}"))
    }

    # Get the command path (to handle nested commands)
    local cmd_path=""
    local i=1
    while [[ $i -lt $COMP_CWORD ]]; do
        case "${COMP_WORDS[$i]}" in
            --*)
                # Skip options and their values
                if [[ "${COMP_WORDS[$i]}" =~ ^--.+=.* ]]; then
                    # Option with value in same word
                    ((i++))
                else
                    # Option with separate value
                    ((i+=2))
                fi
                ;;
            device|d|network|n|topology|t|ops|o|manage|m)
                cmd_path="${COMP_WORDS[$i]}"
                ((i++))
                ;;
            info|profile|list|routing|interface|mpls|vpn|adjacency|neighbors|logs|test-all|list-commands|log-level)
                cmd_path="${cmd_path} ${COMP_WORDS[$i]}"
                ((i++))
                ;;
            *)
                ((i++))
                ;;
        esac
    done

    # Complete based on previous argument
    case "${prev}" in
        --device)
            _complete_devices
            return 0
            ;;
        --devices)
            _complete_devices
            return 0
            ;;
        --output|-o)
            COMPREPLY=($(compgen -W "${output_formats}" -- "${cur}"))
            return 0
            ;;
        --log-level)
            COMPREPLY=($(compgen -W "${log_levels}" -- "${cur}"))
            return 0
            ;;
        --max-workers)
            COMPREPLY=($(compgen -W "1 2 3 4 5 6 7 8 9 10" -- "${cur}"))
            return 0
            ;;
        --inventory|--device-file)
            # File completion
            COMPREPLY=($(compgen -f -- "${cur}"))
            return 0
            ;;
        --module-log-levels)
            # Module log levels format: module1=level,module2=level
            COMPREPLY=($(compgen -W "src.cmd=debug,src.gnmi=info,src.collectors=warning" -- "${cur}"))
            return 0
            ;;
    esac

    # Complete based on command path
    case "${cmd_path}" in
        ""|"gnmibuddy")
            # Main command level
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "${main_opts}" -- "${cur}"))
            else
                COMPREPLY=($(compgen -W "${groups}" -- "${cur}"))
            fi
            ;;
        "device"|"d")
            # Device group level
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --device --output -o --devices --device-file --all-devices --detail" -- "${cur}"))
            else
                COMPREPLY=($(compgen -W "${device_commands}" -- "${cur}"))
            fi
            ;;
        "network"|"n")
            # Network group level
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --device --output -o --devices --device-file --all-devices --protocol --detail" -- "${cur}"))
            else
                COMPREPLY=($(compgen -W "${network_commands}" -- "${cur}"))
            fi
            ;;
        "topology"|"t")
            # Topology group level
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --device --output -o --devices --device-file --all-devices --detail" -- "${cur}"))
            else
                COMPREPLY=($(compgen -W "${topology_commands}" -- "${cur}"))
            fi
            ;;
        "ops"|"o")
            # Ops group level
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --device --output -o --devices --device-file --all-devices --detail" -- "${cur}"))
            else
                COMPREPLY=($(compgen -W "${ops_commands}" -- "${cur}"))
            fi
            ;;
        "manage"|"m")
            # Manage group level
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --level --show --set" -- "${cur}"))
            else
                COMPREPLY=($(compgen -W "${manage_commands}" -- "${cur}"))
            fi
            ;;
        "device info"|"d info")
            # Device info command
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --device --output -o --devices --device-file --all-devices --detail" -- "${cur}"))
            fi
            ;;
        "device profile"|"d profile")
            # Device profile command
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --device --output -o --devices --device-file --all-devices" -- "${cur}"))
            fi
            ;;
        "device list"|"d list")
            # Device list command
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --output -o" -- "${cur}"))
            fi
            ;;
        "network routing"|"n routing")
            # Network routing command
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --device --output -o --devices --device-file --all-devices --protocol --detail" -- "${cur}"))
            fi
            ;;
        "network interface"|"n interface")
            # Network interface command
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --device --output -o --devices --device-file --all-devices --interface --detail" -- "${cur}"))
            fi
            ;;
        "network mpls"|"n mpls")
            # Network MPLS command
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --device --output -o --devices --device-file --all-devices --detail" -- "${cur}"))
            fi
            ;;
        "network vpn"|"n vpn")
            # Network VPN command
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --device --output -o --devices --device-file --all-devices --vrf --detail" -- "${cur}"))
            fi
            ;;
        "topology adjacency"|"t adjacency")
            # Topology adjacency command
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --device --output -o --devices --device-file --all-devices --detail" -- "${cur}"))
            fi
            ;;
        "topology neighbors"|"t neighbors")
            # Topology neighbors command
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --device --output -o --devices --device-file --all-devices --detail" -- "${cur}"))
            fi
            ;;
        "ops logs"|"o logs")
            # Ops logs command
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --device --output -o --devices --device-file --all-devices --filter --severity --since" -- "${cur}"))
            fi
            ;;
        "ops test-all"|"o test-all")
            # Ops test-all command
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --device --output -o --devices --device-file --all-devices" -- "${cur}"))
            fi
            ;;
        "manage list-commands"|"m list-commands")
            # Manage list-commands command
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --output -o" -- "${cur}"))
            fi
            ;;
        "manage log-level"|"m log-level")
            # Manage log-level command
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h --level --show --set" -- "${cur}"))
            fi
            ;;
        *)
            # Default completion
            if [[ ${cur} == -* ]]; then
                COMPREPLY=($(compgen -W "--help -h" -- "${cur}"))
            fi
            ;;
    esac
}

# Register completion function
complete -F _gnmibuddy_completions gnmibuddy

# Also complete for common aliases/variations
complete -F _gnmibuddy_completions gnmibuddy.py

# Installation instructions (for reference)
: '
To install this completion script:

1. Save this file as gnmibuddy-completion.bash
2. Source it in your shell:
   source gnmibuddy-completion.bash

3. Or add it to your shell profile for permanent installation:
   echo "source /path/to/gnmibuddy-completion.bash" >> ~/.bashrc
   # or
   echo "source /path/to/gnmibuddy-completion.bash" >> ~/.bash_profile

4. Restart your shell or run:
   source ~/.bashrc
' 