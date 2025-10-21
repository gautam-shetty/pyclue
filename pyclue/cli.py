import os
import time
import typer
from pathlib import Path

from code_property_graph import CodePropertyGraph
from infer import TypeInference
from constants import AppLogger
import visualize

app = typer.Typer(add_completion=False)

@app.command(help="Generate Code Property Graph for a python repository from a target directory.")
def run(
    target_dir: Path = typer.Argument(..., help="The target directory containing the Python repository."),
    output_dir: Path = typer.Argument(..., help="The directory where the output files will be saved."),
    infer_types: bool = typer.Option(True, help="Flag to enable or disable type inference."),
    export_graph: bool = typer.Option(True, help="Flag to enable or disable exporting the CPG."),
    visualize_graph: bool = typer.Option(False, help="Flag to enable or disable visualization of the CPG."),
    save_log: bool = typer.Option(False, help="Flag to enable or disable saving logs to a file.")
):
    stages = [{"start": time.time()}]
    
    repo_name = os.path.basename(os.path.normpath(target_dir))
    
    if save_log:
        AppLogger.add_file_handler(os.path.join(output_dir, f"{repo_name}.log"))

    cpg = CodePropertyGraph(dir=target_dir)
    cpg.generate_asts()
    cpg.generate_cfgs()
    cpg.generate_dfgs()
    stages.append({"cpg_generation": time.time()})
    
    if export_graph:
        cpg.export(output_path=os.path.join(output_dir, f"{repo_name}.cpg.json"))
        stages.append({"graph_export": time.time()})
    
    if visualize_graph:
        visualize.render(cpg.graph, output_path=os.path.join(output_dir, f"{repo_name}.cpg.png"))
        stages.append({"cpg_visualization": time.time()})
        
        
    if infer_types:
        inf = TypeInference(cpg)
        inf.infer_types()
        stages.append({"type_inference": time.time()})
        
        if export_graph:
            inf.cpg.export(output_path=os.path.join(output_dir, f"{repo_name}_inferred.cpg.json"))
            stages.append({"inferred_graph_export": time.time()})
            
        if visualize_graph:
            visualize.render(inf.cpg.graph, output_path=os.path.join(output_dir, f"{repo_name}_inferred.cpg.png"))
            stages.append({"inferred_cpg_visualization": time.time()})
        
    log_execution_times(stages)

def log_execution_times(stages: list):
    print(f"\n{'Stage':<40} {'Time (s)':<10}")
    print(f"{'-'*50}")
    for i in range(1, len(stages)):
        stage_name = list(stages[i].keys())[0]
        time_taken = stages[i][stage_name] - stages[i-1][list(stages[i-1].keys())[0]]
        print(f"{stage_name:<40} {round(time_taken, 5):<10}")

if __name__ == "__main__":
    app()