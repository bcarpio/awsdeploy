from wtforms import Form, BooleanField, TextField, PasswordField, SelectField, validators

class java_deployment(Form):
    appname = TextField('<strong>App Name:</strong>', [validators.Length(min=4, max=25),validators.Required()])
    version = TextField('<strong>App Version:</strong>', [validators.Length(min=5, max=35),validators.Required()])
    count = TextField('<strong>Count</strong>', [validators.Length(min=1, max=2),validators.Required()])
    size = SelectField('<strong>Size</strong>', choices=[('m1.small', 'm1.small'),('m1.medium','m1.medium'),('m1.large','m1.large'),('m1.xlarge','m1.xlarge')])
    az = SelectField('<strong>Availability Zone:</strong>', choices=[('dev','Development'),('qa','QA'),('usw2a','us-west-2a'),('usw2b','us-west-2b'),('use1a','us-east-1a'),('use1c','us-east-1c')])
