from ncclient import manager
import xmltodict

STUDENT_ID = "66070014"
INTERFACE_NAME = f"Loopback{STUDENT_ID}"


def _get_manager(router_ip):
    """Create and return a NETCONF manager connection"""
    return manager.connect(
        host=router_ip,
        port=830,
        username="admin",
        password="cisco",
        hostkey_verify=False
    )


def _loopback_config_xml(enabled=True, operation="merge"):
    """Generate NETCONF XML configuration for loopback interface"""
    last_three = STUDENT_ID[-3:]
    octet_x = int(last_three[0])
    octet_y = int(last_three[1:])
    ipv4_address = f"172.{octet_x}.{octet_y}.1"
    
    enabled_str = "true" if enabled else "false"
    operation_attr = f'operation="{operation}"' if operation else ""
    
    return f"""
    <config>
        <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
            <interface {operation_attr}>
                <name>{INTERFACE_NAME}</name>
                <description>Loopback interface for student id {STUDENT_ID}</description>
                <type xmlns:ianaift="urn:ietf:params:xml:ns:yang:iana-if-type">ianaift:softwareLoopback</type>
                <enabled>{enabled_str}</enabled>
                <ipv4 xmlns="urn:ietf:params:xml:ns:yang:ietf-ip">
                    <address>
                        <ip>{ipv4_address}</ip>
                        <netmask>255.255.255.0</netmask>
                    </address>
                </ipv4>
            </interface>
        </interfaces>
    </config>
    """


def netconf_edit_config(m, netconf_config):
    """Execute NETCONF edit-config operation"""
    return m.edit_config(target="running", config=netconf_config)


def _interface_exists(router_ip):
    """Check if loopback interface exists using NETCONF"""
    netconf_filter = f"""
    <filter>
        <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
            <interface>
                <name>{INTERFACE_NAME}</name>
            </interface>
        </interfaces>
    </filter>
    """
    
    try:
        m = _get_manager(router_ip)
        netconf_reply = m.get_config(source="running", filter=netconf_filter)
        netconf_reply_dict = xmltodict.parse(netconf_reply.xml)
        m.close_session()
        
        # Check if interface exists in the reply
        interface_data = netconf_reply_dict.get('rpc-reply', {}).get('data', {}).get('interfaces', {}).get('interface')
        
        if interface_data:
            return True
        return False
    except Exception as e:
        # print(f"Error checking interface existence: {e}")
        return False


def create(router_ip, method="Netconf"):
    """Create loopback interface using NETCONF"""
    # Check if interface already exists
    if _interface_exists(router_ip):
        return f"Cannot create: Interface {INTERFACE_NAME.lower()}"
    
    try:
        m = _get_manager(router_ip)
        netconf_config = _loopback_config_xml(enabled=True, operation="merge")
        netconf_reply = netconf_edit_config(m, netconf_config)
        xml_data = netconf_reply.xml
        print(xml_data)
        m.close_session()
        
        if '<ok/>' in xml_data:
            return f"Interface {INTERFACE_NAME.lower()} is created successfully using {method}"
        else:
            return f"Cannot create: Interface {INTERFACE_NAME.lower()}"
    except Exception as e:
        print(f"Error: {e}")
        return "Error: NETCONF create"


def delete(router_ip, method="Netconf"):
    """Delete loopback interface using NETCONF"""
    # Check if interface exists before deleting
    if not _interface_exists(router_ip):
        return f"Cannot delete: Interface {INTERFACE_NAME.lower()}"
    
    netconf_config = f"""
    <config>
        <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
            <interface operation="delete">
                <name>{INTERFACE_NAME}</name>
            </interface>
        </interfaces>
    </config>
    """

    try:
        m = _get_manager(router_ip)
        netconf_reply = netconf_edit_config(m, netconf_config)
        xml_data = netconf_reply.xml
        print(xml_data)
        m.close_session()
        
        if '<ok/>' in xml_data:
            return f"Interface {INTERFACE_NAME.lower()} is deleted successfully using {method}"
        else:
            return f"Cannot delete: Interface {INTERFACE_NAME.lower()}"
    except Exception as e:
        print(f"Error: {e}")
        return "Error: NETCONF delete"


def enable(router_ip, method="Netconf"):
    """Enable loopback interface using NETCONF"""
    # Check if interface exists before enabling
    if not _interface_exists(router_ip):
        return f"Cannot enable: Interface {INTERFACE_NAME.lower()}"
    
    netconf_config = f"""
    <config>
        <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
            <interface>
                <name>{INTERFACE_NAME}</name>
                <enabled>true</enabled>
            </interface>
        </interfaces>
    </config>
    """

    try:
        m = _get_manager(router_ip)
        netconf_reply = netconf_edit_config(m, netconf_config)
        xml_data = netconf_reply.xml
        print(xml_data)
        m.close_session()
        
        if '<ok/>' in xml_data:
            return f"Interface {INTERFACE_NAME.lower()} is enabled successfully using {method}"
        else:
            return f"Cannot enable: Interface {INTERFACE_NAME.lower()}"
    except Exception as e:
        print(f"Error: {e}")
        return "Error: NETCONF enable"


def disable(router_ip, method="Netconf"):
    """Disable loopback interface using NETCONF"""
    # Check if interface exists before disabling
    if not _interface_exists(router_ip):
        return f"Cannot shutdown: Interface {INTERFACE_NAME.lower()}"
    
    netconf_config = f"""
    <config>
        <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
            <interface>
                <name>{INTERFACE_NAME}</name>
                <enabled>false</enabled>
            </interface>
        </interfaces>
    </config>
    """

    try:
        m = _get_manager(router_ip)
        netconf_reply = netconf_edit_config(m, netconf_config)
        xml_data = netconf_reply.xml
        print(xml_data)
        m.close_session()
        
        if '<ok/>' in xml_data:
            return f"Interface {INTERFACE_NAME.lower()} is shutdowned successfully using {method}"
        else:
            return f"Cannot shutdown: Interface {INTERFACE_NAME.lower()}"
    except Exception as e:
        print(f"Error: {e}")
        return "Error: NETCONF disable"


def status(router_ip, method="Netconf"):
    """Get status of loopback interface using NETCONF"""
    if not _interface_exists(router_ip):
        return f"No Interface loopback{STUDENT_ID} (checked by Netconf)"
    netconf_filter = f"""
    <filter>
        <interfaces-state xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
            <interface>
                <name>{INTERFACE_NAME}</name>
            </interface>
        </interfaces-state>
    </filter>
    """

    try:
        m = _get_manager(router_ip)
        # Use Netconf get operation to get interfaces-state information
        netconf_reply = m.get(filter=netconf_filter)
        print(netconf_reply)
        netconf_reply_dict = xmltodict.parse(netconf_reply.xml)
        m.close_session()

        # Check if there is data returned from netconf_reply_dict
        interface_data = netconf_reply_dict.get('rpc-reply', {}).get('data', {}).get('interfaces-state', {}).get('interface')
        
        if interface_data:
            # extract admin_status and oper_status from netconf_reply_dict
            admin_status = interface_data.get('admin-status', 'unknown')
            oper_status = interface_data.get('oper-status', 'unknown')
            
            if admin_status == 'up' and oper_status == 'up':
                return f"Interface {INTERFACE_NAME.lower()} is enabled (checked by {method})"
            elif admin_status == 'down' and oper_status == 'down':
                return f"Interface {INTERFACE_NAME.lower()} is disabled (checked by {method})"
            else:
                return f"Interface {INTERFACE_NAME.lower()} admin-status={admin_status} oper-status={oper_status} (checked by {method})"
    except Exception as e:
        print(f"Error: {e}")
        return "Error: NETCONF status"
