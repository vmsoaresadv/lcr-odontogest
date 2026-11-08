# LCR OdontoGest

Sistema Desktop de Gestão Odontológica e Clínica Integrada.  
**Responsável Técnica:** Dra. Lara Camila (CRO-BA 15247, Irecê - Bahia).

---

## 🚀 Funcionalidades

1. **Autenticação Segura & LGPD:**
   - Controle de perfis de acesso (*Administrador* e *Secretária*).
   - Trilha de auditoria e rastreabilidade imutável de todas as ações.
   - Proteção de dados sensíveis e sigilo profissional.

2. **Gestão de Pacientes & Prontuário:**
   - Cadastro completo com anamnese, histórico de alergias e restrições.
   - Prontuário eletrônico com odontograma e evolução clínica cronológica.
   - Galeria de documentos, exames e radiografias anexadas.

3. **Agenda & Lembretes de Retorno:**
   - Visualização semanal e diária de consultas.
   - Status de agendamento em tempo real (Confirmado, Realizado, Cancelado, etc.).
   - Módulo automatizado de acompanhamento de retornos e pós-operatório.

4. **Sublocação de Consultório (Sala 2):**
   - Agendamento por turnos/horários para profissionais parceiros.
   - Cálculo automático de horas e tarifas.
   - Geração dinâmica de cobrança Pix com QR Code oficial e Copia e Cola.

5. **Controle de Estoque Odontológico:**
   - Rastreabilidade por lote e data de validade.
   - Alertas preventivos de reposição (estoque mínimo) e proximidade de vencimento.
   - Histórico de movimentações de entrada e saída.

6. **Gestão Financeira & Fluxo de Caixa:**
   - Controle unificado de receitas (consultas e sublocações) e despesas.
   - Demonstrativo de Resultados do Exercício (DRE) simplificado.
   - Categorias personalizadas e controle de pagamentos.

7. **Relatórios Gerenciais em PDF:**
   - Emissão de DRE do período, Ficha do Paciente e Inventário de Estoque.
   - Exportação direta em PDF com cabeçalho oficial e rodapé para assinatura profissional.

8. **Backup Seguro & Atualizações:**
   - Backup completo compactado em `.zip` em 1 clique (para pendrive ou nuvem).
   - Verificação e instalação de atualizações automáticas via GitHub Releases.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.12
- **Interface Gráfica:** PySide6 (Qt 6)
- **Banco de Dados:** SQLite com modo WAL (*Write-Ahead Logging*)
- **Segurança:** Bcrypt (hashing de senhas)
- **Compilação:** PyInstaller

---

## 💻 Como Executar em Desenvolvimento

```powershell
# 1. Ativar ambiente virtual
.\.venv\Scripts\Activate.ps1

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar o sistema
python main.py
```

---

## 📦 Como Compilar o Executável Oficial (.exe)

```powershell
python build_exe.py
```
O executável independente será gerado na pasta `dist/LCR-OdontoGest/`.

---

## 🔒 Privacidade e LGPD

Este repositório é de uso estrito e exclusivo da **LCR Clínica Odontológica**.  
Dados de saúde, fichas médicas e arquivos de pacientes nunca são versionados neste repositório.
