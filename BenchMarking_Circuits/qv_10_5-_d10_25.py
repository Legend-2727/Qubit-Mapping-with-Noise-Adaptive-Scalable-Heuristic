import time
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import QuantumVolume
from qiskit_ibm_runtime.fake_provider import FakeWashingtonV2
from qiskit.transpiler import PassManager, CouplingMap
from qiskit.transpiler.passes import SabreLayout, SabreSwap

def generate_qv_circuits(qubit_range, depth_range, num_circuits=10):
    """Generate a set of Quantum Volume circuits with varying parameters."""
    circuits = []
    params = []
    
    for n_qubits in qubit_range:
        for depth in depth_range:
            for i in range(num_circuits):
                # Set a specific seed for reproducibility
                seed = i + (n_qubits * 100) + (depth * 10000)
                qv = QuantumVolume(n_qubits, depth, seed=seed)
                circuits.append(qv)
                params.append((n_qubits, depth, i))
    
    return circuits, params

def transpile_with_sabre(qc, coupling_map, num_trials=1):
    """Transpile a circuit using SABRE with multiple trials."""
    layout_pass = SabreLayout(coupling_map)
    swap_pass = SabreSwap(coupling_map)
    pass_manager = PassManager([layout_pass, swap_pass])
    
    start_time = time.time()
    best_circuit = None
    best_swap_count = float('inf')
    
    for _ in range(num_trials):
        transpiled_qc = pass_manager.run(qc)
        
        # Count SWAP gates (each SWAP is 3 CNOTs)
        swap_count = 0
        for instruction in transpiled_qc.data:
            if instruction.operation.name == 'swap':
                swap_count += 1
        
        if swap_count < best_swap_count:
            best_swap_count = swap_count
            best_circuit = transpiled_qc
    
    transpile_time = time.time() - start_time
    
    return best_circuit, best_swap_count, transpile_time

def benchmark_qv_circuits():
    # Define parameters for QV circuits
    qubit_range = [10, 15, 20, 25, 30]
    depth_range = [10, 15, 20, 25]
    num_circuits_per_config = 10  # Generate 10 circuits per configuration
    
    # Get a backend with enough qubits
    backend = FakeWashingtonV2()  # 127-qubit heavy-hex architecture
    coupling_map = CouplingMap(backend.configuration().coupling_map)
    
    # Generate QV circuits
    print("Generating QV circuits...")
    circuits, params = generate_qv_circuits(qubit_range, depth_range, num_circuits_per_config)
    print(f"Generated {len(circuits)} QV circuits")
    
    # Results storage
    results = []
    
    # Run benchmarks
    print("Running benchmarks...")
    for i, (qc, (n_qubits, depth, idx)) in enumerate(zip(circuits, params)):
        print(f"Processing circuit {i+1}/{len(circuits)}: {n_qubits} qubits, depth {depth}, idx {idx}")
        
        # Run with single trial
        transpiled_qc, swap_count, transpile_time = transpile_with_sabre(qc, coupling_map)
        
        # Store results in a dictionary
        result = {
            'qubits': n_qubits,
            'depth': depth,
            'circuit_idx': idx,
            'swap_count': swap_count,
            'transpile_time': transpile_time,
            'original_depth': qc.depth(),
            'transpiled_depth': transpiled_qc.depth()
        }
        
        results.append(result)
        
        # Print current result
        print(f"  Swap count: {swap_count}, Time: {transpile_time:.4f}s, Original depth: {qc.depth()}, Transpiled depth: {transpiled_qc.depth()}")
    
    # Save results to a file
    with open('qv_benchmark_results.txt', 'w') as f:
        for result in results:
            f.write(f"{result}\n")
    
    return results

if __name__ == "__main__":
    results = benchmark_qv_circuits()
    print("Benchmarking complete!")
