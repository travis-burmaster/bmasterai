"""Example Airflow DAG for testing the Streamlit MCP integration"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.task_group import TaskGroup
import random
import time

# Default arguments for the DAG
default_args = {
    'owner': 'data_team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email': ['admin@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5)
}

# Define the DAG
dag = DAG(
    'example_data_pipeline',
    default_args=default_args,
    description='An example data pipeline for demonstration',
    schedule='@daily',
    catchup=False,
    tags=['example', 'etl', 'data_pipeline']
)

# Python functions for tasks
def extract_data(**context):
    """Simulate data extraction"""
    print("Extracting data from source...")
    time.sleep(random.randint(1, 3))
    
    # Simulate occasional failures
    if random.random() < 0.1:  # 10% chance of failure
        raise Exception("Data extraction failed: Connection timeout")
    
    # Push data to XCom
    data_size = random.randint(1000, 5000)
    context['task_instance'].xcom_push(key='record_count', value=data_size)
    print(f"Extracted {data_size} records")
    return data_size

def transform_data(**context):
    """Simulate data transformation"""
    ti = context['task_instance']
    record_count = ti.xcom_pull(task_ids='extract_data', key='record_count')
    
    print(f"Transforming {record_count} records...")
    time.sleep(random.randint(2, 4))
    
    # Simulate data quality checks
    invalid_records = random.randint(0, int(record_count * 0.05))
    valid_records = record_count - invalid_records
    
    ti.xcom_push(key='valid_records', value=valid_records)
    ti.xcom_push(key='invalid_records', value=invalid_records)
    
    print(f"Transformation complete: {valid_records} valid, {invalid_records} invalid")
    return valid_records

def load_data(**context):
    """Simulate data loading"""
    ti = context['task_instance']
    valid_records = ti.xcom_pull(task_ids='transform_data', key='valid_records')
    
    print(f"Loading {valid_records} records to destination...")
    time.sleep(random.randint(1, 3))
    
    # Simulate occasional failures
    if random.random() < 0.05:  # 5% chance of failure
        raise Exception("Data load failed: Database connection error")
    
    print(f"Successfully loaded {valid_records} records")
    return valid_records

def generate_report(**context):
    """Generate a summary report"""
    ti = context['task_instance']
    
    # Pull all metrics
    extracted = ti.xcom_pull(task_ids='extract_data', key='record_count')
    valid = ti.xcom_pull(task_ids='transform_data', key='valid_records')
    invalid = ti.xcom_pull(task_ids='transform_data', key='invalid_records')
    
    report = f"""
    Pipeline Summary Report
    ======================
    Execution Date: {context['ds']}
    
    Records Extracted: {extracted}
    Valid Records: {valid}
    Invalid Records: {invalid}
    Success Rate: {(valid/extracted*100):.2f}%
    
    Status: COMPLETED
    """
    
    print(report)
    return report

# Define tasks
with dag:
    # Start task
    start = EmptyOperator(
        task_id='start',
        doc="Mark the beginning of the pipeline"
    )
    
    # Data extraction
    extract = PythonOperator(
        task_id='extract_data',
        python_callable=extract_data,
        doc="Extract data from source systems"
    )
    
    # Data quality check
    quality_check = BashOperator(
        task_id='data_quality_check',
        bash_command='echo "Running data quality checks..." && sleep 2',
        doc="Perform data quality validation"
    )
    
    # Transform data with task group
    with TaskGroup('transform_tasks') as transform_group:
        transform = PythonOperator(
            task_id='transform_data',
            python_callable=transform_data,
            doc="Transform and clean data"
        )
        
        validate = BashOperator(
            task_id='validate_transformation',
            bash_command='echo "Validating transformed data..." && sleep 1',
            doc="Validate transformation results"
        )
        
        transform >> validate
    
    # Load data
    load = PythonOperator(
        task_id='load_data',
        python_callable=load_data,
        doc="Load data to destination"
    )
    
    # Generate report
    report = PythonOperator(
        task_id='generate_report',
        python_callable=generate_report,
        doc="Generate pipeline execution report"
    )
    
    # Send notification
    notify = BashOperator(
        task_id='send_notification',
        bash_command='echo "Sending completion notification..."',
        trigger_rule='all_done',  # Run regardless of upstream success/failure
        doc="Send pipeline completion notification"
    )
    
    # End task
    end = EmptyOperator(
        task_id='end',
        trigger_rule='all_done',
        doc="Mark the end of the pipeline"
    )
    
    # Define task dependencies
    start >> extract >> quality_check >> transform_group >> load >> report >> notify >> end


# Create another example DAG for ML workflows
ml_dag = DAG(
    'ml_model_training',
    default_args=default_args,
    description='Machine learning model training pipeline',
    schedule='@weekly',
    catchup=False,
    tags=['ml', 'training', 'model']
)

def prepare_dataset(**context):
    """Prepare dataset for training"""
    print("Preparing dataset...")
    time.sleep(2)
    dataset_size = random.randint(10000, 50000)
    context['task_instance'].xcom_push(key='dataset_size', value=dataset_size)
    return dataset_size

def train_model(**context):
    """Train ML model"""
    ti = context['task_instance']
    dataset_size = ti.xcom_pull(task_ids='prepare_dataset', key='dataset_size')
    
    print(f"Training model on {dataset_size} samples...")
    time.sleep(random.randint(5, 10))
    
    # Simulate model metrics
    accuracy = random.uniform(0.85, 0.95)
    ti.xcom_push(key='accuracy', value=accuracy)
    
    print(f"Model trained with accuracy: {accuracy:.4f}")
    return accuracy

def evaluate_model(**context):
    """Evaluate model performance"""
    ti = context['task_instance']
    accuracy = ti.xcom_pull(task_ids='train_model', key='accuracy')
    
    print(f"Evaluating model with accuracy {accuracy:.4f}...")
    time.sleep(2)
    
    # Decide if model should be deployed
    deploy = accuracy > 0.90
    ti.xcom_push(key='deploy_decision', value=deploy)
    
    return deploy

def deploy_model(**context):
    """Deploy model to production"""
    ti = context['task_instance']
    deploy = ti.xcom_pull(task_ids='evaluate_model', key='deploy_decision')
    
    if deploy:
        print("Deploying model to production...")
        time.sleep(3)
        print("Model deployed successfully!")
    else:
        print("Model did not meet deployment criteria")
        raise Exception("Model accuracy too low for deployment")

with ml_dag:
    ml_start = EmptyOperator(task_id='start')
    
    prepare = PythonOperator(
        task_id='prepare_dataset',
        python_callable=prepare_dataset
    )
    
    train = PythonOperator(
        task_id='train_model',
        python_callable=train_model
    )
    
    evaluate = PythonOperator(
        task_id='evaluate_model',
        python_callable=evaluate_model
    )
    
    deploy = PythonOperator(
        task_id='deploy_model',
        python_callable=deploy_model
    )
    
    ml_end = EmptyOperator(
        task_id='end',
        trigger_rule='all_done'
    )
    
    ml_start >> prepare >> train >> evaluate >> deploy >> ml_end