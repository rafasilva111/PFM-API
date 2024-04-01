

## Extensions recommended

### Markdown Support:
PyCharm supports Markdown files out of the box, so you should be able to open and edit .md files without any additional setup. However, if you want advanced Markdown preview features, you can install a Markdown plugin.


#### Go to Settings/Preferences:

For Windows and Linux: File > Settings
For macOS: PyCharm > Preferences

#### Install Markdown Plugin:

In the Settings/Preferences dialog, navigate to Plugins.

Click on the Marketplace tab.

Search for "Markdown" in the search bar.

Find the "Markdown support" plugin and click Install or Enable (if it's already installed but disabled).

Restart PyCharm to apply the changes.

Now you should have enhanced Markdown support in PyCharm, including preview features.

## Good Practices


### Errors


´´´

errors = {}
if "username" in e.args[1]:
    errors["username"]=["Username is already being used."]
elif "email" in e.args[1]:
    errors["email"] = ["Email is already being used."]

return Response(status=400, response=json.dumps({"errors":errors}), mimetype="application/json")

´´´




## Run flask commands on windows

-> powershell navigate to folder

-> flask <command-name>

### Troubleshoot:

-> pip install flask-cli

pip install flask-cli


drop database db_name
create database db_name



ACTIVIDADE = {
            'sedentario': ['Pouco ou nenhum execício', 1.2],
            'leve': ['Execício de 1 a 3 vezes', 1.375],
            'moderado': ['Execício 4-5 vezes/semana', 1.465],
            'ativo': ['Execício diario ou exercícios intensos 3-4 vezes/semana', 1.55],
            'muito_ativo': ['Exercícios intensos 6-7 vezes/semana', 1.725],
            'extra_ativo': ['Execício intesso diário, ou te um trabalho muito fisico', 1.9]
        }