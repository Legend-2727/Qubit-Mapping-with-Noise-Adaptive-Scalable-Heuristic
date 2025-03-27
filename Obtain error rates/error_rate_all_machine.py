import json
from datetime import datetime
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_ibm_runtime.fake_provider import FakeOslo  # For retired backends

def get_all_backend_errors():
    """Retrieve error metrics for all available IBM Quantum backends"""
    service = QiskitRuntimeService()
    backends = service.backends()
    
    results = {}
    
    for backend in backends:
        try:
            print(f"\nProcessing {backend.name}...")
            
            # Handle status via method call
            status = backend.status()
            props = backend.properties()
            
            if not props:
                print(f"Skipping {backend.name}: No properties available")
                continue
                
            # Qubit metrics
            qubit_errors = []
            for qubit in range(backend.num_qubits):
                qubit_data = {
                    "qubit": qubit,
                    "T1": safe_get(props.t1, qubit),
                    "T2": safe_get(props.t2, qubit),
                    "readout_error": safe_get(props.readout_error, qubit),
                    "frequency": safe_get(props.frequency, qubit)
                }
                qubit_errors.append(qubit_data)
            
            # Gate errors
            gate_errors = []
            for gate in props.gates:
                if gate.gate == "cx":
                    error = next((p.value for p in gate.parameters if p.name == "gate_error"), None)
                    gate_data = {
                        "gate": gate.gate,
                        "qubits": gate.qubits,
                        "error_rate": error,
                        "gate_length": gate.gate_length
                    }
                    gate_errors.append(gate_data)
            
            # Store results
            results[backend.name] = {
                "operational": status.operational,
                "pending_jobs": status.pending_jobs,
                "qubits": qubit_errors,
                "cx_gates": gate_errors,
                "last_update": props.last_update_date.isoformat() if props.last_update_date else None
            }
            
        except Exception as e:
            print(f"Error processing {backend.name}: {str(e)}")
            # For retired systems, use fake provider data
            if "retired" in str(e).lower():
                fake_backend = FakeOslo()  # Replace with appropriate fake backend
                results[backend.name] = get_fake_backend_data(fake_backend)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"ibm_errors_{timestamp}.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return results

def safe_get(func, qubit):
    """Safely retrieve properties with error handling"""
    try:
        value = func(qubit)
        return f"{value:.2e}" if isinstance(value, float) else str(value)
    except Exception:
        return "N/A"

def get_fake_backend_data(fake_backend):
    """Get data for retired systems using fake provider"""
    props = fake_backend.properties()
    return {
        "operational": False,
        "pending_jobs": 0,
        "qubits": [
            {
                "T1": f"{props.t1(qubit):.2e}" if props.t1(qubit) else "N/A",
                "T2": f"{props.t2(qubit):.2e}" if props.t2(qubit) else "N/A",
                "readout_error": f"{props.readout_error(qubit):.4f}" 
            } for qubit in range(fake_backend.num_qubits)
        ],
        "cx_gates": [
            {
                "error_rate": gate.error
            } for gate in props.gates if gate.gate == "cx"
        ]
    }

if __name__ == "__main__":
    error_data = get_all_backend_errors()
    print(json.dumps(error_data, indent=2))
