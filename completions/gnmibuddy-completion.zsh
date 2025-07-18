#compdef gnmibuddy

# ZSH completion for gNMIBuddy CLI
# Save this file as gnmibuddy-completion.zsh and add it to your fpath

_gnmibuddy() {
    local context curcontext="$curcontext" state line
    typeset -A opt_args

    # Helper function to get device names
    _gnmibuddy_devices() {
        local devices
        devices=(${(f)"$(gnmibuddy device list 2>/dev/null | grep -v '^Device' | grep -v '^-' | awk '{print $1}')"})
        _describe 'devices' devices
    }

    # Helper function for output formats
    _gnmibuddy_output_formats() {
        local formats
        formats=(
            'json:JSON output format'
            'yaml:YAML output format' 
            'table:Table output format (default)'
        )
        _describe 'output formats' formats
    }

    # Helper function for log levels
    _gnmibuddy_log_levels() {
        local levels
        levels=(
            'debug:Debug level logging'
            'info:Info level logging'
            'warning:Warning level logging'
            'error:Error level logging'
        )
        _describe 'log levels' levels
    }

    # Main CLI options
    local main_options=(
        '(-h --help)'{-h,--help}'[Show help message]'
        '(-V --version)'{-V,--version}'[Show version information]'
        '--version-detailed[Show detailed version information]'
        '--log-level[Set global logging level]:log level:_gnmibuddy_log_levels'
        '--module-log-levels[Set module-specific log levels]:module levels:'
        '--structured-logging[Enable structured JSON logging]'
        '--quiet-external[Reduce noise from external libraries]'
        '--all-devices[Run command on all devices in inventory]'
        '--max-workers[Maximum number of concurrent workers]:workers:(1 2 3 4 5 6 7 8 9 10)'
        '--inventory[Path to inventory JSON file]:inventory file:_files -g "*.json"'
    )

    # Common command options
    local common_options=(
        '(-h --help)'{-h,--help}'[Show help message]'
        '--device[Device name from inventory]:device:_gnmibuddy_devices'
        '(-o --output)'{-o,--output}'[Output format]:format:_gnmibuddy_output_formats'
        '--devices[Comma-separated list of device names]:devices:'
        '--device-file[Path to file containing device names]:device file:_files'
        '--all-devices[Run command on all devices in inventory]'
    )

    # Define the command structure
    _arguments -C \
        $main_options \
        '1: :_gnmibuddy_commands' \
        '*:: :->args'

    case $state in
        args)
            case $words[1] in
                device|d)
                    _gnmibuddy_device
                    ;;
                network|n)
                    _gnmibuddy_network
                    ;;
                topology|t)
                    _gnmibuddy_topology
                    ;;
                ops|o)
                    _gnmibuddy_ops
                    ;;
                manage|m)
                    _gnmibuddy_manage
                    ;;
            esac
            ;;
    esac
}

# Main command groups
_gnmibuddy_commands() {
    local commands
    commands=(
        'device:Device management commands'
        'd:Device management commands (alias)'
        'network:Network protocol commands'
        'n:Network protocol commands (alias)'
        'topology:Network topology commands'
        't:Network topology commands (alias)'
        'ops:Operational commands'
        'o:Operational commands (alias)'
        'manage:Management commands'
        'm:Management commands (alias)'
    )
    _describe 'commands' commands
}

# Device group commands
_gnmibuddy_device() {
    local context curcontext="$curcontext" state line
    typeset -A opt_args

    _arguments \
        $common_options \
        '--detail[Show detailed information]' \
        '1: :_gnmibuddy_device_commands' \
        '*:: :->device_args'

    case $state in
        device_args)
            case $words[1] in
                info)
                    _arguments \
                        $common_options \
                        '--detail[Show detailed system information]'
                    ;;
                profile)
                    _arguments \
                        $common_options
                    ;;
                list)
                    _arguments \
                        '(-h --help)'{-h,--help}'[Show help message]' \
                        '(-o --output)'{-o,--output}'[Output format]:format:_gnmibuddy_output_formats'
                    ;;
            esac
            ;;
    esac
}

_gnmibuddy_device_commands() {
    local commands
    commands=(
        'info:Get system information from a network device'
        'profile:Get device profile and role information'
        'list:List all available devices in the inventory'
    )
    _describe 'device commands' commands
}

# Network group commands
_gnmibuddy_network() {
    local context curcontext="$curcontext" state line
    typeset -A opt_args

    _arguments \
        $common_options \
        '--detail[Show detailed information]' \
        '--protocol[Protocol filter]:protocol:' \
        '1: :_gnmibuddy_network_commands' \
        '*:: :->network_args'

    case $state in
        network_args)
            case $words[1] in
                routing)
                    _arguments \
                        $common_options \
                        '--detail[Show detailed routing information]' \
                        '--protocol[Routing protocol filter]:protocol:(bgp isis ospf static)'
                    ;;
                interface)
                    _arguments \
                        $common_options \
                        '--detail[Show detailed interface information]' \
                        '--interface[Specific interface]:interface:'
                    ;;
                mpls)
                    _arguments \
                        $common_options \
                        '--detail[Show detailed MPLS information]'
                    ;;
                vpn)
                    _arguments \
                        $common_options \
                        '--detail[Show detailed VPN information]' \
                        '--vrf[Specific VRF]:vrf:'
                    ;;
            esac
            ;;
    esac
}

_gnmibuddy_network_commands() {
    local commands
    commands=(
        'routing:Get routing protocol information (BGP, ISIS, OSPF)'
        'interface:Get interface status and configuration'
        'mpls:Get MPLS forwarding and label information'
        'vpn:Get VPN/VRF configuration and status'
    )
    _describe 'network commands' commands
}

# Topology group commands
_gnmibuddy_topology() {
    local context curcontext="$curcontext" state line
    typeset -A opt_args

    _arguments \
        $common_options \
        '--detail[Show detailed information]' \
        '1: :_gnmibuddy_topology_commands' \
        '*:: :->topology_args'

    case $state in
        topology_args)
            case $words[1] in
                adjacency)
                    _arguments \
                        $common_options \
                        '--detail[Show detailed adjacency information]'
                    ;;
                neighbors)
                    _arguments \
                        $common_options \
                        '--detail[Show detailed neighbor information]'
                    ;;
            esac
            ;;
    esac
}

_gnmibuddy_topology_commands() {
    local commands
    commands=(
        'adjacency:Get complete topology adjacency information'
        'neighbors:Get direct neighbor information via LLDP/CDP'
    )
    _describe 'topology commands' commands
}

# Ops group commands
_gnmibuddy_ops() {
    local context curcontext="$curcontext" state line
    typeset -A opt_args

    _arguments \
        $common_options \
        '--detail[Show detailed information]' \
        '1: :_gnmibuddy_ops_commands' \
        '*:: :->ops_args'

    case $state in
        ops_args)
            case $words[1] in
                logs)
                    _arguments \
                        $common_options \
                        '--filter[Log filter pattern]:pattern:' \
                        '--severity[Log severity level]:severity:(emergency alert critical error warning notice info debug)' \
                        '--since[Show logs since timestamp]:timestamp:'
                    ;;
                test-all)
                    _arguments \
                        $common_options
                    ;;
            esac
            ;;
    esac
}

_gnmibuddy_ops_commands() {
    local commands
    commands=(
        'logs:Retrieve and filter device logs'
        'test-all:Test all gNMI operations on a device'
    )
    _describe 'ops commands' commands
}

# Manage group commands
_gnmibuddy_manage() {
    local context curcontext="$curcontext" state line
    typeset -A opt_args

    _arguments \
        '(-h --help)'{-h,--help}'[Show help message]' \
        '1: :_gnmibuddy_manage_commands' \
        '*:: :->manage_args'

    case $state in
        manage_args)
            case $words[1] in
                list-commands)
                    _arguments \
                        '(-h --help)'{-h,--help}'[Show help message]' \
                        '(-o --output)'{-o,--output}'[Output format]:format:_gnmibuddy_output_formats'
                    ;;
                log-level)
                    _arguments \
                        '(-h --help)'{-h,--help}'[Show help message]' \
                        '--level[Log level to set]:level:_gnmibuddy_log_levels' \
                        '--show[Show current log levels]' \
                        '--set[Set log level]:level:_gnmibuddy_log_levels'
                    ;;
            esac
            ;;
    esac
}

_gnmibuddy_manage_commands() {
    local commands
    commands=(
        'list-commands:List all available CLI commands'
        'log-level:Configure logging levels dynamically'
    )
    _describe 'manage commands' commands
}

# Register the completion function
_gnmibuddy "$@"

# Installation instructions (for reference)
: '
To install this completion script:

1. Save this file as gnmibuddy-completion.zsh
2. Make sure it is in your fpath. You can add it by creating a directory for completions:
   mkdir -p ~/.zsh/completions
   cp gnmibuddy-completion.zsh ~/.zsh/completions/_gnmibuddy

3. Add the completion directory to your fpath in ~/.zshrc:
   fpath=(~/.zsh/completions $fpath)

4. Initialize the completion system in ~/.zshrc (if not already done):
   autoload -Uz compinit
   compinit

5. Restart your shell or reload your configuration:
   source ~/.zshrc

Alternative installation:
You can also source this file directly in your ~/.zshrc:
   source /path/to/gnmibuddy-completion.zsh
' 