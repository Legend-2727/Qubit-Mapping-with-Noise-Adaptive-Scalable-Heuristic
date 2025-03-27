import time
import random
import numpy as np
from qiskit import QuantumCircuit
from qiskit_ibm_runtime.fake_provider import FakeWashingtonV2
from qiskit.transpiler import PassManager, CouplingMap
from qiskit.transpiler.passes import SabreLayout, SabreSwap

def create_bv_circuit(n_qubits, hidden_string=None):
    """
    Create a Bernstein-Vazirani circuit for the given number of qubits.
    
    Args:
        n_qubits (int): Number of qubits (excluding the ancilla qubit)
        hidden_string (str, optional): Binary string to encode. If None, a random string is generated.
    
    Returns:
        QuantumCircuit: The BV circuit
    """
    # If no hidden string is provided, generate a random one
    if hidden_string is None:
        hidden_string = ''.join(random.choice('01') for _ in range(n_qubits))
    
    # Create quantum circuit with n+1 qubits (n for the input, 1 for the ancilla)
    qc = QuantumCircuit(n_qubits + 1, n_qubits)
    
    # Initialize the ancilla qubit in state |1⟩
    qc.x(n_qubits)
    
    # Apply Hadamard gates to all qubits
    for i in range(n_qubits + 1):
        qc.h(i)
    
    # Apply the oracle (CNOT gates where the hidden string has 1s)
    for i in range(n_qubits):
        if hidden_string[i] == '1':
            qc.cx(i, n_qubits)
    
    # Apply Hadamard gates to the input qubits
    for i in range(n_qubits):
        qc.h(i)
    
    # Measure the input qubits
    qc.measure(range(n_qubits), range(n_qubits))
    
    return qc, hidden_string

def transpile_with_sabre(qc, coupling_map):
    """
    Transpile a circuit using SABRE layout and swap passes.
    
    Args:
        qc (QuantumCircuit): The quantum circuit to transpile
        coupling_map (CouplingMap): The coupling map of the target device
    
    Returns:
        tuple: (transpiled_circuit, transpile_time, swap_count)
    """
    layout_pass = SabreLayout(coupling_map)
    swap_pass = SabreSwap(coupling_map)
    pass_manager = PassManager([layout_pass, swap_pass])
    
    start_time = time.time()
    transpiled_qc = pass_manager.run(qc)
    transpile_time = time.time() - start_time
    
    # Count SWAP gates
    swap_count = 0
    for instruction in transpiled_qc.data:
        if instruction.operation.name == 'swap':
            swap_count += 1
    
    return transpiled_qc, transpile_time, swap_count

def benchmark_bv_circuits():
    """
    Benchmark SABRE on Bernstein-Vazirani circuits of varying sizes.
    """
    # Define the range of qubits to test
    qubit_range = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
    num_circuits_per_size = 5  # Number of random circuits per qubit size
    
    # Get a backend with enough qubits
    backend = FakeWashingtonV2()  # 127-qubit heavy-hex architecture
    coupling_map = CouplingMap(backend.configuration().coupling_map)
    
    # Results storage
    results = []
    
    # Run benchmarks
    print("Running Bernstein-Vazirani benchmarks...")
    for n_qubits in qubit_range:
        print(f"\nTesting with {n_qubits} qubits:")
        
        for i in range(num_circuits_per_size):
            # Create a BV circuit with a random hidden string
            qc, hidden_string = create_bv_circuit(n_qubits)
            
            print(f"  Circuit {i+1}/{num_circuits_per_size} - Hidden string: {hidden_string}")
            
            try:
                # Transpile the circuit
                transpiled_qc, transpile_time, swap_count = transpile_with_sabre(qc, coupling_map)
                
                # Record results
                result = {
                    'qubits': n_qubits,
                    'circuit_idx': i,
                    'hidden_string': hidden_string,
                    'swap_count': swap_count,
                    'transpile_time': transpile_time,
                    'original_depth': qc.depth(),
                    'transpiled_depth': transpiled_qc.depth(),
                    'original_size': len(qc.data),
                    'transpiled_size': len(transpiled_qc.data)
                }
                
                results.append(result)
                
                # Print current result
                print(f"    Swap count: {swap_count}, Time: {transpile_time:.4f}s")
                print(f"    Original depth: {qc.depth()}, Transpiled depth: {transpiled_qc.depth()}")
                print(f"    Original size: {len(qc.data)}, Transpiled size: {len(transpiled_qc.data)}")
                
            except Exception as e:
                print(f"    Error: {e}")
    
    # Save results to a file
    with open('bv_benchmark_results.txt', 'w') as f:
        for result in results:
            f.write(f"{result}\n")
    
    # Calculate and print summary statistics
    print("\nSummary Statistics:")
    for n_qubits in qubit_range:
        qubit_results = [r for r in results if r['qubits'] == n_qubits]
        if qubit_results:
            avg_swap = sum(r['swap_count'] for r in qubit_results) / len(qubit_results)
            avg_time = sum(r['transpile_time'] for r in qubit_results) / len(qubit_results)
            avg_depth_increase = sum((r['transpiled_depth'] - r['original_depth']) for r in qubit_results) / len(qubit_results)
            
            print(f"Qubits: {n_qubits}")
            print(f"  Avg SWAP count: {avg_swap:.2f}")
            print(f"  Avg transpile time: {avg_time:.4f}s")
            print(f"  Avg depth increase: {avg_depth_increase:.2f}")
    
    return results

if __name__ == "__main__":
    results = benchmark_bv_circuits()
    print("Benchmarking complete!")
