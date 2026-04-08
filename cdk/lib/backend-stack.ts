import * as cdk from "aws-cdk-lib";
import * as ec2 from "aws-cdk-lib/aws-ec2";
import * as ecr from "aws-cdk-lib/aws-ecr";
import * as ecs from "aws-cdk-lib/aws-ecs";
import * as logs from "aws-cdk-lib/aws-logs";
import * as secretsmanager from "aws-cdk-lib/aws-secretsmanager";
import * as ecs_patterns from "aws-cdk-lib/aws-ecs-patterns";
import { Construct } from "constructs";

export class BackendStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // VPC with 2 AZs and 1 NAT gateway
    const vpc = new ec2.Vpc(this, "CerelienVpc", {
      maxAzs: 2,
      natGateways: 1,
    });

    // ECR Repository
    const ecrRepo = new ecr.Repository(this, "CerelienApiRepo", {
      repositoryName: "cerelien-api",
      lifecycleRules: [
        {
          maxImageCount: 10,
          description: "Keep last 10 images",
        },
      ],
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // ECS Cluster with Container Insights
    const cluster = new ecs.Cluster(this, "CerelienCluster", {
      vpc,
      clusterName: "cerelien-cluster",
      containerInsights: true,
    });

    // Secrets Manager secret for environment variables
    const secret = new secretsmanager.Secret(this, "CerelienApiSecret", {
      secretName: "cerelien-api/env",
      description: "Environment variables for Cerelien API",
      generateSecretString: {
        secretStringTemplate: JSON.stringify({
          NEON_DATABASE_URL: "CHANGE_ME",
          OPENAI_API_KEY: "CHANGE_ME",
          TWILIO_ACCOUNT_SID: "CHANGE_ME",
          TWILIO_AUTH_TOKEN: "CHANGE_ME",
          TWILIO_PHONE_NUMBER: "CHANGE_ME",
          TWILIO_API_KEY_SID: "CHANGE_ME",
          TWILIO_API_KEY_SECRET: "CHANGE_ME",
          TWILIO_TWIML_APP_SID: "CHANGE_ME",
        }),
        generateStringKey: "_placeholder",
      },
    });

    // CloudWatch Log Group
    const logGroup = new logs.LogGroup(this, "CerelienApiLogGroup", {
      logGroupName: "/ecs/cerelien-api",
      retention: logs.RetentionDays.ONE_MONTH,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Application Load Balanced Fargate Service
    const fargateService =
      new ecs_patterns.ApplicationLoadBalancedFargateService(
        this,
        "CerelienApiService",
        {
          cluster,
          cpu: 512,
          memoryLimitMiB: 1024,
          desiredCount: 1,
          taskImageOptions: {
            image: ecs.ContainerImage.fromEcrRepository(ecrRepo, "latest"),
            containerPort: 8000,
            logDriver: ecs.LogDrivers.awsLogs({
              logGroup,
              streamPrefix: "cerelien-api",
            }),
            secrets: {
              NEON_DATABASE_URL: ecs.Secret.fromSecretsManager(
                secret,
                "NEON_DATABASE_URL"
              ),
              OPENAI_API_KEY: ecs.Secret.fromSecretsManager(
                secret,
                "OPENAI_API_KEY"
              ),
              TWILIO_ACCOUNT_SID: ecs.Secret.fromSecretsManager(
                secret,
                "TWILIO_ACCOUNT_SID"
              ),
              TWILIO_AUTH_TOKEN: ecs.Secret.fromSecretsManager(
                secret,
                "TWILIO_AUTH_TOKEN"
              ),
              TWILIO_PHONE_NUMBER: ecs.Secret.fromSecretsManager(
                secret,
                "TWILIO_PHONE_NUMBER"
              ),
              TWILIO_API_KEY_SID: ecs.Secret.fromSecretsManager(
                secret,
                "TWILIO_API_KEY_SID"
              ),
              TWILIO_API_KEY_SECRET: ecs.Secret.fromSecretsManager(
                secret,
                "TWILIO_API_KEY_SECRET"
              ),
              TWILIO_TWIML_APP_SID: ecs.Secret.fromSecretsManager(
                secret,
                "TWILIO_TWIML_APP_SID"
              ),
            },
            environment: {
              APP_ENV: "production",
              LOG_LEVEL: "INFO",
              FIREBASE_PROJECT_ID: "cerelien-ai",
            },
          },
          circuitBreaker: {
            rollback: true,
          },
        }
      );

    // Health check configuration
    fargateService.targetGroup.configureHealthCheck({
      path: "/health",
    });

    // Auto-scaling: 1-10 tasks, 70% CPU target
    const scaling = fargateService.service.autoScaleTaskCount({
      minCapacity: 1,
      maxCapacity: 10,
    });

    scaling.scaleOnCpuUtilization("CpuScaling", {
      targetUtilizationPercent: 70,
    });

    // Outputs
    new cdk.CfnOutput(this, "LoadBalancerDNS", {
      value: fargateService.loadBalancer.loadBalancerDnsName,
      description: "Application Load Balancer DNS",
    });

    new cdk.CfnOutput(this, "EcrRepoUri", {
      value: ecrRepo.repositoryUri,
      description: "ECR Repository URI",
    });
  }
}
