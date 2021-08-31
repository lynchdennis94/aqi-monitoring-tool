import ssl

import utilities
import purpleairhook
import time
import smtplib
import json
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


def send_email(crossing_above_threshold, server, port, username, password, current_aqi,
               threshold_aqi, target_email):
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

        # Send off email
        try:
            print(f"Sending email to {target_email}")
            msg['To'] = target_email
            server.sendmail(username, target_email, msg.as_string())
        except smtplib.SMTPException:
            print("Couldn't send email")

    finally:
        server.quit()


def main():
    currently_above_threshold = False
    print("Running")
    while True:
        # Load necessary config information for this iteration
        config_dict = utilities.load_config_data()
        purple_air_hook = purpleairhook.PurpleAirHook()

        # Get the information from purple air
        response = purple_air_hook.get_bounded_sensors_data()
        json_response = json.loads(response.text)
        response_data = json_response["data"]
        aqi_values = []

        # Calculate the AQI and compare to threshold
        for item in response_data:
            aqi = purpleairhook.get_aqi_value('pm2.5', item[2])
            aqi_values.append(aqi)

        aqi_values.sort()
        filter_values = aqi_values[1:-1]
        averaged_aqi = sum(filter_values) / len(filter_values)
        rounded_aqi = round(averaged_aqi)
        threshold = config_dict[aqi_threshold_config_key]

        should_send_email = False
        config_dict[send_emails_config_key]
        if rounded_aqi >= threshold and not currently_above_threshold:
            # We've crossed above the threshold - send an email
            should_send_email = True
            currently_above_threshold = True
        elif rounded_aqi < threshold and currently_above_threshold:
            # We've dipped below the threshold - send an email
            should_send_email = True
            currently_above_threshold = False

        if should_send_email:
            if config_dict[send_emails_config_key]:
                target_emails = config_dict[target_emails_config_key]
            else:
                target_emails = [config_dict[smtp_username_config_key]]
            for email in target_emails:
                send_email(currently_above_threshold,
                           config_dict[smtp_server_config_key],
                           config_dict[smtp_port_config_key],
                           config_dict[smtp_username_config_key],
                           config_dict[smtp_password_config_key],
                           rounded_aqi,
                           threshold,
                           email)

        # Sleep until next iteration
        time.sleep(config_dict[sleep_timer_config_key])


if __name__ == '__main__':
    main()
