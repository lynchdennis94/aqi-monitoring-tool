import ssl

import requests
import time
import json
import smtplib
from email.message import EmailMessage

api_key_config_key = 'api-key'
sleep_timer_config_key = 'sleep-timer'
target_emails_config_key = 'emails-for-notifications'
aqi_threshold_config_key = 'AQI-threshold'
send_emails_config_key = 'send-email-notifications'
smtp_server_config_key = 'smtp-server'
smtp_port_config_key = 'smtp-port'
smtp_username_config_key = 'smtp-username'
smtp_password_config_key = 'smtp-password'


def load_config_data():
    with open('config.json', 'r') as config_file:
        json_data = config_file.read()

    return json.loads(json_data)


def get_purpleair_data(api_key):
    return 0


def calculate_aqi(data):
    return 0


def send_email(send_real_emails, crossing_above_threshold, server, port, username, password, current_aqi,
               threshold_aqi, target_emails=None):
    server = smtplib.SMTP(server, port)
    server.ehlo()
    server.starttls(context=ssl.create_default_context())
    server.login(username, password)

    try:
        # Set up the common message components
        msg = EmailMessage()
        msg['From'] = username

        # Construct the message based on whether we crossed above or below the threshold
        if crossing_above_threshold:
            print(f"Crossing above threshold {threshold_aqi} with AQI currently at {current_aqi}")
            msg['Subject'] = "[AQI Monitoring] AQI Crossed above threshold"
            body = f"The AQI is currently at {current_aqi} and has crossed above the threshold of {threshold_aqi}. " \
                   "Consider closing the windows!"
            msg.set_content(body)
        else:
            print(f"Dropping below threshold {threshold_aqi} with AQI currently at {current_aqi}")
            msg['Subject'] = "[AQI Monitoring] AQI Dropped below threshold"
            body = f"The AQI is currently at {current_aqi} and has dropped below the threshold of {threshold_aqi}. " \
                   "You can open the windows back up!"
            msg.set_content(body)

        # Determine recipients and send off email(s)
        if send_real_emails:
            for target_email in target_emails:
                try:
                    print(f"Sending email to {target_email}")
                    msg['To'] = target_email
                    server.sendmail(username, target_email, msg.as_string())
                except smtplib.SMTPException:
                    print("Couldn't send email")
        else:
            try:
                print(f"Sending email to {username}")
                msg['To'] = username
                server.sendmail(username, username, msg.as_string())
            except smtplib.SMTPException:
                print("Couldn't send email")

    finally:
        server.quit()


def main():
    currently_above_threshold = False
    while True:
        # Load necessary config information for this iteration
        config_dict = load_config_data()

        # Get the information from purple air
        purple_air_data = get_purpleair_data(config_dict[api_key_config_key])

        # Calculate the AQI and compare to threshold
        aqi = calculate_aqi(purple_air_data)
        threshold = config_dict[aqi_threshold_config_key]

        if aqi > threshold and not currently_above_threshold:
            # We've crossed above the threshold - send an email
            send_email(config_dict[send_emails_config_key],
                       True,
                       config_dict[smtp_server_config_key],
                       config_dict[smtp_port_config_key],
                       config_dict[smtp_username_config_key],
                       config_dict[smtp_password_config_key],
                       aqi,
                       threshold,
                       config_dict[target_emails_config_key])
            currently_above_threshold = True
        elif aqi < threshold and currently_above_threshold:
            # We've dipped below the threshold - send an email
            send_email(config_dict[send_emails_config_key],
                       False,
                       config_dict[smtp_server_config_key],
                       config_dict[smtp_port_config_key],
                       config_dict[smtp_username_config_key],
                       config_dict[smtp_password_config_key],
                       aqi,
                       threshold,
                       config_dict[target_emails_config_key])
            currently_above_threshold = False

        # Sleep until next iteration
        print(config_dict)
        time.sleep(config_dict[sleep_timer_config_key])


if __name__ == '__main__':
    main()
