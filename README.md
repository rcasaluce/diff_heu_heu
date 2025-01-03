

# New Diff Model for White-box Model Validation with Statistical Model Checking and Process Mining

## Overview


`diff_heu_heu.py` is a Python command-line application designed to create a diff model, apply the Heuristics Miner algorithm, compare "old" and "new" process models, and generate visualizations highlighting their differences. 
This tool is particularly useful for analyzing and visualizing the differences in simulated models.

## Definition

Consider two versions of a model, referred to as the *1<sup>st</sup>* model and the *2<sup>nd</sup>* model, each obtained by simulating potentially distinct variants of a formal specification. Unlike the original diff model, which relied on automatically generated graphical representations of the procedural part of the model, the new diff model is derived directly from the simulated event logs of the two model variants under comparison.

**Let:**

- **L1** be the event log obtained from simulating the *1<sup>st</sup>* model.
- **L2** be the event log obtained from simulating the *2<sup>nd</sup>* model.

Each log L<sub>i</sub> contains sequences of events, with each event including at least a case ID, a timestamp, and an activity name. If the underlying formalism distinguishes between states and activities, a preprocessing step merges states and transitions into a unified set of activities for process discovery. Otherwise, if only activities are available, no such merging is required.

We apply the **Heuristics Miner (HM)** algorithm to each log separately, obtaining two Heuristics Nets (HNs):

- **H1** = (N1, E1, freq1) from L1  
- **H2** = (N2, E2, freq2) from L2

**Here:**

- N<sub>i</sub> is a set of nodes representing discovered activities, as well as special start and end nodes.
- E<sub>i</sub> is a set of edges capturing directly-follows relationships among nodes in N<sub>i</sub>.
- freq<sub>i</sub> assigns frequencies to each edge in E<sub>i</sub>.

The new diff model **D** is defined as:

D = (N_D, E_D, lN, lE)

**Where:**

- **N_D** = N1 ∪ N2 (the union of the nodes from both HNs).
- **E_D** = E1 ∪ E2 (the union of all edges).
- **lN** : N_D → { common, 1st-only, 2nd-only } labels each node based on whether it appears in both models (common), only in the 1<sup>st</sup> model (1st-only), or only in the 2<sup>nd</sup> model (2nd-only).
- **lE** : E_D → { common, 1st-only, 2nd-only } labels each edge similarly.

**In the new diff model:**

- **Black nodes and edges** (*common*) appear in both \( H_1 \) and \( H_2 \).
- **Red nodes and edges** (*1<sup>st</sup>-only*) represent behaviors and transitions present only in the *1<sup>st</sup> model*.
- **Blue nodes and edges** (*2<sup>nd</sup>-only*) indicate behaviors and transitions introduced in or unique to the *2<sup>nd</sup> model*.

This new diff model allows direct comparison of two mined models without relying on a known procedural representation.


## Features

- **Pre-processing Logs**: Cleans and formats event logs from CSV files.
- **Heuristics Miner**: Applies the Heuristics Miner algorithm to discover process models.
- **Difference Analysis**: Compares old and new process models to identify differences.
- **Visualization**: Generates PDF graphs highlighting the differences between models.

## Prerequisites

- **Python**: Ensure you have Python 3.6 or higher installed. You can download Python from [python.org](https://www.python.org/downloads/).
- **Graphviz**: This tool requires Graphviz to generate visualizations.

## Installation

### 1. Clone the Repository

First, clone this repository or download the `diff_heu_heu.py` script to your local machine.

```bash
git clone https://github.com/rcasaluce/diff_heu_heu.git
cd process_logs_cli
```

### 2. Set Up a Virtual Environment

It's recommended to use a virtual environment to manage dependencies. Below are instructions for creating and activating a virtual environment on different operating systems.

#### **Windows**

1. **Open Command Prompt**:

   Press `Win + R`, type `cmd`, and press `Enter`.

2. **Navigate to the Project Directory**:

   ```bash
   cd path\to\diff_heu_heu
   ```

3. **Create a Virtual Environment**:

   ```bash
   python -m venv venv
   ```

4. **Activate the Virtual Environment**:

   ```bash
   venv\Scripts\activate
   ```

#### **macOS and Linux**

1. **Open Terminal**.

2. **Navigate to the Project Directory**:

   ```bash
   cd path/to/diff_heu_heu
   ```

3. **Create a Virtual Environment**:

   ```bash
   python3 -m venv venv
   ```

4. **Activate the Virtual Environment**:

   ```bash
   source venv/bin/activate
   ```

### 3. Install Python Dependencies

With the virtual environment activated, install the required Python libraries using `pip`.

```bash
pip install -r requirements.txt
```

Alternatively, if a `requirements.txt` file is not provided, install the dependencies manually:

```bash
pip install pm4py pandas numpy graphviz pydotplus pygraphviz
```

> **Note**: If you encounter issues installing `pygraphviz`, ensure that Graphviz is properly installed on your system and that the Graphviz binaries are accessible via your system's PATH.

### 4. Install Graphviz

Graphviz is required for generating the visualization PDFs.

#### **Windows**

1. **Download Graphviz**:

   Download the Graphviz installer from the [Graphviz Download Page](https://graphviz.org/download/).

2. **Install Graphviz**:

   Run the installer and follow the on-screen instructions.

3. **Add Graphviz to PATH**:

   - Open the Start Menu, search for "Environment Variables," and select "Edit the system environment variables."
   - Click on "Environment Variables."
   - Under "System variables," find and select the `Path` variable, then click "Edit."
   - Click "New" and add the path to the Graphviz `bin` directory (e.g., `C:\Program Files\Graphviz\bin`).
   - Click "OK" to save changes.

4. **Verify Installation**:

   Open Command Prompt and run:

   ```bash
   dot -V
   ```

   You should see the Graphviz version information.

#### **macOS**

1. **Using Homebrew**:

   If you have Homebrew installed, you can install Graphviz with:

   ```bash
   brew install graphviz
   ```

2. **Verify Installation**:

   Open Terminal and run:

   ```bash
   dot -V
   ```

   You should see the Graphviz version information.

#### **Linux**

1. **Using APT (Debian/Ubuntu)**:

   ```bash
   sudo apt-get update
   sudo apt-get install graphviz
   ```

2. **Using YUM (CentOS/RHEL)**:

   ```bash
   sudo yum install graphviz
   ```

3. **Verify Installation**:

   Open Terminal and run:

   ```bash
   dot -V
   ```

   You should see the Graphviz version information.

## Usage

### Command-Line Arguments

The script accepts the following command-line arguments:

- `--file_path_old`: **(Required)** Path to the `first_model.csv` file.
- `--file_path_new`: **(Required)** Path to the `second_model.csv` file.
- `--output_full`: **(Optional)** Filename for the complete differences PDF. Default: `complete_differences`.
- `--output_filtered_full`: **(Optional)** Filename for the filtered complete differences PDF. Default: `filtered_differences`.

### Running the Script

Ensure that your virtual environment is activated and that all dependencies are installed.

#### **Basic Usage**

```bash
python diff_heu_heu.py \
    --file_path_old "path/to/first_model.csv" \
    --file_path_new "path/to/second_model.csv"
```

#### **Specifying Output Filenames**

```bash
python diff_heu_heu.py \
    --file_path_old "path/to/first_model.csv" \
    --file_path_new "path/to/second_model.csv" \
    --output_full "complete_differences" \
    --output_filtered_full "filtered_differences"
```

This will generate:

- `complete_differences.pdf`
- `filtered_differences.pdf`

### Run Experiments 

#### Paper: Roberto Casaluce, Max Tschaikowski, Andrea Vandin:
#### White-Box Validation of Collective Adaptive Systems by Statistical Model Checking and Process Mining. ISoLA (1) 2024: 204-222

Assuming your CSV files are located in `./logs/`, run:

```bash
python diff_heu_heu.py \
    --file_path_old "./logs/robot_main_first.csv" \
    --file_path_new "./logs/robot_main_second.csv" \
    --output_full "complete_differences" \
    --output_filtered_full "filtered_differences"
```

### Output

After execution, the script will generate the following PDF files in the current directory (or in the specified output path):

- `complete_differences.pdf`: Visualizes the complete differences between the old and new process models.
- `filtered_differences.pdf`: Visualizes the filtered differences.

## Troubleshooting

### Common Issues

1. **Module Not Found Errors**:

   - **Issue**: Errors indicating missing modules such as `pm4py`, `pygraphviz`, etc.
   - **Solution**: Ensure that all dependencies are installed in your virtual environment.

     ```bash
     pip install pm4py pandas numpy graphviz pydotplus pygraphviz
     ```

2. **Graphviz Installation Issues**:

   - **Issue**: Errors related to Graphviz when generating visualizations.
   - **Solution**: Ensure that Graphviz is installed correctly and that its executables are accessible via your system's PATH.

3. **Permission Errors on Unix-like Systems**:

   - **Issue**: Permission denied errors when trying to make the script executable.
   - **Solution**: Ensure you have the necessary permissions or use `sudo` if appropriate.

4. **Incorrect File Paths**:

   - **Issue**: Errors indicating that the specified CSV files do not exist.
   - **Solution**: Verify that the paths provided to `--file_path_old` and `--file_path_new` are correct.

     ```bash
     ls path/to/first_model.csv
     ls path/to/second_model.csv
     ```

5. **Python Version Compatibility**:

   - **Issue**: Errors due to incompatible Python versions.
   - **Solution**: Ensure you are using Python 3.6 or higher.

     ```bash
     python --version
     ```

### Advanced Logging

For more detailed logs, consider modifying the script to use Python's `logging` module instead of `print` statements.

## Extensibility

The script is modular, allowing you to easily add more functionalities or modify existing ones as per your requirements. For example, you can extend the script to handle additional event log files, integrate other process mining algorithms, or enhance the visualization features.

## Contribution

Contributions are welcome! Please fork the repository and submit a pull request with your enhancements.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
