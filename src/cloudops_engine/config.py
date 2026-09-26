import os

from dotenv import load_dotenv


load_dotenv()


AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
EC2_INSTANCE_ID = os.getenv("EC2_INSTANCE_ID")
CPU_THRESHOLD = float(os.getenv("CPU_THRESHOLD", "90.0"))