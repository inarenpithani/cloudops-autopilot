import os

from dotenv import load_dotenv


load_dotenv()


AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

EC2_INSTANCE_ID = os.getenv("EC2_INSTANCE_ID")

CPU_THRESHOLD = float(os.getenv("CPU_THRESHOLD", "90.0"))

SNS_TOPIC_ARN = os.getenv(
    "SNS_TOPIC_ARN",
    "arn:aws:sns:ap-south-1:298785331841:cloudops-autopilot-incidents",
)