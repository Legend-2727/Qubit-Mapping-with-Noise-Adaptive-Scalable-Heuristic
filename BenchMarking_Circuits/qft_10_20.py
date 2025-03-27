import time
import numpy as np
from qiskit import QuantumCircuit
from qiskit_ibm_runtime.fake_provider import FakeWashingtonV2
from qiskit.transpiler import PassManager, CouplingMap
from qiskit.transpiler.passes import SabreLayout, SabreSwap

def create_qft_circuit(n_qubits):
    qc = QuantumCircuit(n_qubits)
    for j in range(n_qubits):
        for k in range(j):
            qc.cp(np.pi/float(2**(j-k)), k, j)
        qc.h(j)
    return qc

def transpile_with_sabre(qc, coupling_map):
    layout_pass = SabreLayout(coupling_map)
    swap_pass = SabreSwap(coupling_map)
    pass_manager = PassManager([layout_pass, swap_pass])
    
    start_time = time.time()
    transpiled_qc = pass_manager.run(qc)
    transpile_time = time.time() - start_time
    
    return transpiled_qc, transpile_time

# Get a backend with enough qubits
backend = FakeWashingtonV2()
coupling_map = CouplingMap(backend.configuration().coupling_map)

# Run benchmarks for 10-20 qubits
for n_qubits in range(10, 21):
    try:
        qc = create_qft_circuit(n_qubits)
        transpiled_qc, transpile_time = transpile_with_sabre(qc, coupling_map)
        
        print(f"\n--- QFT Circuit with {n_qubits} qubits ---")
        print(f"Transpilation Time: {transpile_time:.4f} seconds")
        print(f"Original Circuit Depth: {qc.depth()}")
        print(f"Transpiled Circuit Depth: {transpiled_qc.depth()}")
        print(f"Number of Operations: {len(transpiled_qc.data)}")
    except Exception as e:
        print(f"Error with {n_qubits} qubits: {e}")
