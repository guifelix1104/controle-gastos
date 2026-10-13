const inputMes = document.getElementById("mes");
const inputData = document.getElementById("data");
const form = document.getElementById("form-transacao");
const mensagem = document.getElementById("mensagem");
const avisoVazio = document.getElementById("aviso-vazio");

const CORES = {
  "Moradia": "#4e79a7",
  "Alimentação": "#f28e2b",
  "Transporte": "#59a14f",
  "Lazer": "#b07aa1",
  "Saúde": "#e15759",
  "Educação": "#76b7b2",
  "Outros": "#9c9c9c",
  "Sem categoria": "#d3d3d3",
};

let grafico = null;

function formatarMoeda(valor) {
  return valor.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function mesAtual() {
  const hoje = new Date();
  const mes = String(hoje.getMonth() + 1).padStart(2, "0");
  return `${hoje.getFullYear()}-${mes}`;
}

function hojeISO() {
  const dia = String(new Date().getDate()).padStart(2, "0");
  return `${mesAtual()}-${dia}`;
}

function desenharGrafico(categorias) {
  const vazio = categorias.length === 0;
  avisoVazio.hidden = !vazio;

  if (grafico) {
    grafico.destroy();
  }
  if (vazio) {
    return;
  }

  grafico = new Chart(document.getElementById("grafico"), {
    type: "pie",
    data: {
      labels: categorias.map((c) => c.categoria),
      datasets: [
        {
          data: categorias.map((c) => c.total),
          backgroundColor: categorias.map((c) => CORES[c.categoria] || "#cccccc"),
        },
      ],
    },
    options: {
      plugins: {
        tooltip: {
          callbacks: {
            label: (item) => `${item.label}: ${formatarMoeda(item.parsed)}`,
          },
        },
      },
    },
  });
}

async function carregarResumo() {
  const resposta = await fetch(`/resumo/?mes=${inputMes.value}`);
  const dados = await resposta.json();

  document.getElementById("total-renda").textContent = formatarMoeda(dados.total_renda);
  document.getElementById("total-gastos").textContent = formatarMoeda(dados.total_gastos);

  const saldo = document.getElementById("saldo");
  saldo.textContent = formatarMoeda(dados.saldo);
  saldo.className = dados.saldo >= 0 ? "positivo" : "negativo";

  desenharGrafico(dados.gastos_por_categoria);
}

form.addEventListener("submit", async (evento) => {
  evento.preventDefault();

  const corpo = {
    descricao: document.getElementById("descricao").value,
    valor: parseFloat(document.getElementById("valor").value),
    tipo: document.getElementById("tipo").value,
    data: inputData.value,
    fixa: document.getElementById("fixa").checked,
  };

  const resposta = await fetch("/transacoes/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(corpo),
  });

  if (resposta.ok) {
    const criada = await resposta.json();
    mensagem.textContent = criada.categoria_nome
      ? `Adicionado em ${criada.categoria_nome}`
      : "Adicionado!";

    form.reset();
    inputData.value = hojeISO();
    inputMes.value = criada.data.slice(0, 7);
    carregarResumo();
  } else {
    mensagem.textContent = "Erro ao adicionar. Confira os campos.";
  }
});

inputMes.addEventListener("change", carregarResumo);

inputMes.value = mesAtual();
inputData.value = hojeISO();
carregarResumo();