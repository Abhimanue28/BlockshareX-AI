import ipfshttpclient
import os

# Connect to local IPFS daemon (ensure IPFS Desktop or daemon is running)
try:
    client = ipfshttpclient.connect()  # Default: /dns/localhost/tcp/5001/http
except Exception as e:
    raise ConnectionError("Make sure IPFS daemon is running: " + str(e))


# 📤 Upload file to IPFS and return its hash
def upload_to_ipfs(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError("File not found: " + file_path)

    result = client.add(file_path)
    return result['Hash']


# 📥 Download file from IPFS to local disk
def download_from_ipfs(ipfs_hash, output_path="downloads"):
    os.makedirs(output_path, exist_ok=True)
    file_path = os.path.join(output_path, ipfs_hash)

    client.get(ipfs_hash, target=file_path)
    return file_path
