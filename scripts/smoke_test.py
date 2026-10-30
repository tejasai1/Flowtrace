from flowtrace.providers import get_provider

provider = get_provider()

print("Models available to your account:")
for name in provider.list_models():
    print("  ", name)

print(f"\nSending a test message to {provider.model} ...")
reply = provider.complete([
    {"role": "user", "content": "Reply with exactly: FlowTrace connected"}
])
print("Reply:", reply.content)