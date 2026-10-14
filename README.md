# Greenroom

Loja de jogos digitais em Django, com cadastro de clientes, acompanhamento de compras e painel de gerência.

## Executar localmente

```bash
python3 -m pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py seed_store
python3 manage.py createsuperuser
python3 manage.py runserver
```

Abra `http://127.0.0.1:8000`. O cadastro público cria contas de cliente. Para criar um gerente, entre em `/admin/`, abra **Usuários**, escolha a conta e altere o papel para **Gerente**. O superusuário criado com `createsuperuser` administra usuários, produtos e pedidos pelo Admin.

## Áreas

- `/`: catálogo com busca, filtros e registro de pedidos.
- `/criar-conta/` e `/entrar/`: cadastro e autenticação.
- `/minha-conta/`: perfil, resumo e compras recentes do cliente autenticado.
- `/minhas-compras/`: pedidos do cliente autenticado.
- `/gerencia/compras/`: todos os pedidos e atualização de status para gerentes e administradores.
- `/admin/`: administração do Django.

As compras são registradas como pedidos novos; esta versão não integra um provedor de pagamento. O catálogo de demonstração pode ser criado ou atualizado com `python3 manage.py seed_store`.