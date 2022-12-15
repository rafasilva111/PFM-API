# PFM_Flask_API


# Comandos 

C:\Users\rafae\Desktop\Projetos\MyProjects\PFM_flask_api\venv\Scripts\activate

python -m virtualenv venv

python -m eb

eb open

eb terminate flask-env

# BrainStorm

altura
peso
idade
genero
actividade:
	sedentario: little or no exercice
	leve: exercicio de 1 a 3 vezes
	moderado: execicio 4-5 vezes/semana
	ativo: execicio diario ou exercicios intensos 3-4 vezes/semana
	muito ativo: exercicio muito intesso diário, ou te um trabalho muito fisico 

'absolutamente nenhum': ['Taxa metabólica basal',1],
      'sedentario': [ 'Pouco ou nenhum exercicio',1.2],
	'leve': ['Exercicio de 1 a 3 vezes',1.375],
	'moderado': ['execicio 4-5 vezes/semana',1.465],
	'ativo': ['execicio diario ou exercicios intensos 3-4 vezes/semana',1.55],
	'muito ativo': ['exercissio intesso diário, ou te um trabalho muito fisico',]

exercicio: 15-30 minutes of elevated heart rate activity.
exercicio intenso: 45-120 minutes of elevated heart rate activity.
exercicio muito intesso: 2+ hours of elevated heart rate activity.

/full_model?altura=180&idade=20&genero=m&peso=60&atividade=leve&goal=0

two types of goals:
	inseridos pelo proprio
	sugeridos pela app:
		perder 1
		perder 0.5
		perder 0
		ganhar 0.5
		ganhar 1
