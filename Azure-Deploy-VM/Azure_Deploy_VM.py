import os
import traceback

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.compute.models import DiskCreateOption

from msrestazure.azure_exceptions import CloudError

from haikunator import Haikunator

haikunator = Haikunator()

# Set Azure variables
LOCATION = 'westeurope'
RESOURCE_GROUP = 'Python-Test'
VNET_NAME = 'Python-VNet'
VNET_ADDRESS_SPACE = '10.1.0.0/16'
SUBNET_PREFIX = '10.1.0.0/24'
SUBNET_NAME = 'Python-VNet-Subnet1'
VM_NAME = 'Python-VM1'
OS_DISK = 'osdisk1'
STORAGE_ACCOUNT = haikunator.haikunate(delimiter = '')
IP_CONFIG = 'ipconfig'
NIC_NAME = VM_NAME + '-nic'
VM_SIZE = 'Standard_A0'
USERNAME = 'labuser'
PASSWORD = 'M1crosoft123'
AZURE_SUBSCRIPTION_ID = '7855847d-d89f-4bc7-93c4-59623eab44cd'
AZURE_CLIENT_ID = '69e81861-af05-424c-89b7-d303e778d0b8'
AZURE_CLIENT_SECRET = 'M1crosoft123'
AZURE_TENANT_ID = '72f988bf-86f1-41af-91ab-2d7cd011db47'


VM_DETAILS = {
    'linux': {
        'publisher': 'Canonical',
        'offer': 'UbuntuServer',
        'sku': '16.04.0-LTS',
        'version': 'latest'
    },
    'windows': {
        'publisher': 'MicrosoftWindowsServerEssentials',
        'offer': 'WindowsServerEssentials',
        'sku': 'WindowsServerEssentials',
        'version': 'latest'
    }
}

def main():
    credentials, subscriptionID = getCredentials()

    # Create resource, compute & network clients using the service principal credentials
    resourceClient = ResourceManagementClient(credentials, subscriptionID)
    networkClient = NetworkManagementClient(credentials, subscriptionID)
    computeClient = ComputeManagementClient(credentials, subscriptionID)

    # Create resource group
    print('Creating resource group...')
    resourceClient.resource_groups.create_or_update(RESOURCE_GROUP, {'location': LOCATION})
    print('Done.')

    # Create networking and get NIC
    nic = createNetworking(networkClient)

    # Create virtual machine
    createVM(computeClient, nic)



def getCredentials():
    subscriptionID = AZURE_SUBSCRIPTION_ID
    credentials = ServicePrincipalCredentials(
        client_id=AZURE_CLIENT_ID,
        secret=AZURE_CLIENT_SECRET,
        tenant=AZURE_TENANT_ID 
    )
    return credentials, subscriptionID



def createNetworking(networkClient):

    # Create virtual network,
    print('Creating virtual network...')
    vnet = networkClient.virtual_networks.create_or_update(
        RESOURCE_GROUP,
        VNET_NAME,
        {
            'location': LOCATION,
            'address_space': {
                'address_prefixes': ['10.1.0.0/16']
                }
            }
        )
    print('Done.')

    # Create subnet
    print('Creating subnet...')
    subnet = networkClient.subnets.create_or_update(
        RESOURCE_GROUP,
        VNET_NAME,
        SUBNET_NAME,
        {'address_prefix': SUBNET_PREFIX}
        )
    subnet_info = subnet.result()
    print('Done.')

    # Create network interface for VM
    print('Creating NIC...')
    nic = networkClient.network_interfaces.create_or_update(
        RESOURCE_GROUP,
        NIC_NAME,
        {
            'location': LOCATION,
            'ip_configurations': [{
                'name': IP_CONFIG,
                'subnet': {
                    'id': subnet_info.id
                    }
                }]
            })
    print('Done.')

    # Return NIC info
    return nic.result()

def createVM(computeClient, nic):

    # Get VM parameters
    parameters = vmParameters(VM_DETAILS['linux'], nic.id)

    # Create the VM and start it
    print('Creating virtual machine...')
    vm = computeClient.virtual_machines.create_or_update(
        RESOURCE_GROUP,VM_NAME,parameters
        )
    vm.wait()

    print('Done.')

    print('Starting virtual machine...')
    vmStart = computeClient.virtual_machines.start(RESOURCE_GROUP, VM_NAME)
    vmStart.wait()
    print('Done.')
    
def vmParameters(vmDetails, nicID):
    return {
        'location': LOCATION,
        'os_profile': {
            'computer_name': VM_NAME,
            'admin_username': USERNAME,
            'admin_password': PASSWORD
            },
        'hardware_profile': {
            'vm_size': VM_SIZE
            },
        'storage_profile': {
            'image_reference': {
                'publisher': vmDetails['publisher'],
                'offer': vmDetails['offer'],
                'sku': vmDetails['sku'],
                'version': vmDetails['version']
                }
            },
        'network_profile': {
            'network_interfaces': [{
                'id': nicID
                }]                                
            }
        }

if __name__ == "__main__":
    main()