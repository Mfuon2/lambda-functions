# AWS Lambda Document Analysis with Amazon Textract

## Purpose

This AWS Lambda function analyzes documents using Amazon Textract. It can process both base64-encoded images and images stored in Amazon S3, extracting information based on the document type specified in the event payload.

## Prerequisites

- AWS account with Lambda, S3, and Textract permissions.
- Python 3.x environment with `boto3` installed.

## Functionality

The Lambda function performs the following tasks:

1. **Document Retrieval**:
    - Supports images provided as base64-encoded strings or from S3 buckets.

2. **Document Analysis**:
    - Uses Amazon Textract to analyze the document and extract key-value pairs.

3. **Information Extraction**:
    - Depending on the `document_type`, it extracts specific information:
        - **BUSINESS_REGISTRATION**: Extracts business number, name, and registration date.
        - **CERTIFICATE_OF_INCORPORATION**: Extracts company name.
        - **Other Types**: Returns key-value pairs found in the document.

## Setup

1. **Install Dependencies**:
   Ensure you have `boto3` and other required libraries installed.

   ```bash
   pip install boto3
   ```

## Configuration

1. **Set Up AWS Credentials**:
   Ensure that AWS credentials are configured properly. You can set them up using the AWS CLI or by configuring environment variables. The Lambda function requires access to Amazon Textract and S3 services.

   ```bash
   aws configure
   ```

## Lambda Permissions

Ensure that your Lambda function has the necessary IAM role with the following policies:

- **Textract Access**: Permissions to use the `AnalyzeDocument` operation.
- **S3 Access**: Permissions to access objects in S3 if you're retrieving images from an S3 bucket.

### Example IAM Policy

Below is an example IAM policy that grants permissions for Textract and S3 access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "textract:AnalyzeDocument"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket-name/*"
    }
  ]
}
```


## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For any inquiries or support, feel free to contact [Mfuon Leonard](mailto:mfolee@gmail.com).

Thank you for using our project! We hope it helps you securely integrate AWS Textract with your applications. Happy coding!
