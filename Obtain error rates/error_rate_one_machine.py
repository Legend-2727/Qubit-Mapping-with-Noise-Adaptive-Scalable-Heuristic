from qiskit_ibm_runtime import QiskitRuntimeService

# Initialize with saved credentials (first time setup)
# QiskitRuntimeService.save_account(channel="ibm_quantum", token="YOUR_API_TOKEN")

service = QiskitRuntimeService()
backend = service.backend("ibm_brisbane")  # Current recommended backend

# Get error rates
properties = backend.properties()
print(f"Backend: {backend.name}")
print(f"Qubits: {backend.num_qubits}")

print("\nQubit Properties:")
for qubit in range(backend.num_qubits):
    t1 = properties.t1(qubit)
    t2 = properties.t2(qubit)
    readout_error = properties.readout_error(qubit)
    print(f"Qubit {qubit}:")
    print(f"  T1 = {t1:.2e} s")
    print(f"  T2 = {t2:.2e} s")
    print(f"  Readout error = {readout_error:.4f}")

print("\nCNOT Gate Errors:")
for gate in properties.gates:
    if gate.gate == "cx":
        for param in gate.parameters:
            if param.name == "gate_error":
                print(f"{gate.gate} {gate.qubits}: {param.value:.4f}")
