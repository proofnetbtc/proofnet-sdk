"""Quick check: print Proofnet node status via BTCore read lane."""
from proofnet_sdk.client import ProofnetClient
client = ProofnetClient()
try:
    print("Node status:", client.status())
except Exception as e:
    print(f"Could not reach node: {e}")
