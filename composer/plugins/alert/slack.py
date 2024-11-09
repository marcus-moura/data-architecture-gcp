from airflow.providers.slack.operators.slack_webhook import SlackWebhookOperator

SLACK_CHANNEL = 'airflow-alert'
SLACK_CONN_ID = 'slack_conn_id'

def build_slack_message(context, options, local_dt):
    """Constrói a mensagem do Slack com alerta de falha."""
    
    task_instance = context.get('task_instance')
    log_url = task_instance.log_url
    task_id = task_instance.task_id
    dag_id = task_instance.dag_id

    slack_msg = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{options['icon']} *{options['title']}*"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Task*: {task_id}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Dag*: {dag_id}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Execution Date*: {local_dt.strftime('%Y/%m/%d %H:%M:%S')}"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "Ver Logs"
                    },
                    "url": log_url,
                    "style": "danger" 
                }
            ]
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "*Note*: This is an automatic alert generated from Airflow."
                }
            ]
        }
    ]
    
    return slack_msg

def send_fail_alert_slack(context):
    """Envia um alerta para o Slack quando uma tarefa falha no Airflow."""
    
    # Configurações do ícone e título
    options = {
        'icon': ':red_circle:',
        'title': 'Task Failed in Airflow'
    }

    # Obter a data de execução ajustada para o fuso horário correto
    local_dt = context.get('data_interval_start').astimezone()

    slack_msg = build_slack_message(context, options, local_dt)

    failed_alert = SlackWebhookOperator(
        task_id='slack_alert',
        slack_webhook_conn_id=SLACK_CONN_ID,
        channel=SLACK_CHANNEL,
        blocks=slack_msg,
        username='airflow',
        timeout=5
    )

    return failed_alert.execute(context=context)
