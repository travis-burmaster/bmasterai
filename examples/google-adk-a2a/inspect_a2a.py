import inspect
from a2a.client import A2AClient
import a2a.types

print("--- A2AClient.get_task signature ---")
try:
    print(inspect.signature(A2AClient.get_task))
except Exception as e:
    print(e)

print("\n--- a2a.types contents ---")
print(dir(a2a.types))
