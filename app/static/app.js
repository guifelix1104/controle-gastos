const inputMes = document.getElementById("mes");
const inputData = document.getElementById("data");
const form = document.getElementById("form-transacao");
const mensagem = document.getElementById("mensagem");
const avisoVazio = document.getElementById("aviso-vazio");

const listaTransacoes = document.getElementById("lista-transacoes");
const avisoSemTransacoes = document.getElementById("aviso-sem-transacoes");
const mensagemFixas = document.getElementById("mensagem-fixas");
const botaoGerarFixas = document.getElementById("btn-gerar-fixas");

const listaMetas = document.getElementById("lista-metas");
const avisoSemMetas = document.getElementById("aviso-sem-metas");
const formMeta = document.getElementById("form-meta");
const mensagemMeta = document.getElementById("mensagem-meta");

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

function formatarData(iso) {
  const [ano, mes, dia] = iso.split("-");
  return `${dia}/${mes}/${ano}`;
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

function criarElemento(tag, classe, texto) {
  const elemento = document.createElement(tag);
  if (classe) {
    elemento.className = classe;
  }
  if (texto !== undefined) {
    elemento.textContent = texto;
  }
  return elemento;
}

function mensagemDeErro(erro) {
  return typeof erro.detail === "string" ? erro.detail : "Confira os campos.";
}

/* ---------- Resumo do mês e gráfico ---------- */

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

/* ---------- Transações do mês ---------- */

function criarLinhaTransacao(transacao) {
  const ehRenda = transacao.tipo === "renda";
  const linha = criarElemento("li", "linha");

  linha.appendChild(
    criarElemento("span", "linha-data", formatarData(transacao.data).slice(0, 5))
  );

  const descricao = criarElemento("span", "linha-descricao", transacao.descricao);
  if (transacao.fixa) {
    descricao.appendChild(criarElemento("span", "tag", "fixa"));
  }
  linha.appendChild(descricao);

  const categoria = transacao.categoria_nome || (ehRenda ? "Renda" : "Sem categoria");
  linha.appendChild(criarElemento("span", "linha-categoria", categoria));

  const sinal = ehRenda ? "+" : "-";
  linha.appendChild(
    criarElemento(
      "span",
      ehRenda ? "valor-renda" : "valor-gasto",
      `${sinal} ${formatarMoeda(transacao.valor)}`
    )
  );

  const acoes = criarElemento("span", "linha-acoes");

  if (transacao.fixa) {
    const parar = criarElemento("button", "secundario pequeno", "Parar de repetir");
    parar.type = "button";
    parar.addEventListener("click", () => pararFixa(transacao.id));
    acoes.appendChild(parar);
  }

  const excluir = criarElemento("button", "secundario pequeno", "Excluir");
  excluir.type = "button";
  excluir.addEventListener("click", () => excluirTransacao(transacao.id));
  acoes.appendChild(excluir);

  linha.appendChild(acoes);
  return linha;
}

async function carregarTransacoes() {
  const resposta = await fetch(`/transacoes/?mes=${inputMes.value}`);
  const transacoes = await resposta.json();

  listaTransacoes.replaceChildren();
  avisoSemTransacoes.hidden = transacoes.length > 0;

  for (const transacao of transacoes) {
    listaTransacoes.appendChild(criarLinhaTransacao(transacao));
  }
}

async function atualizarMes() {
  await Promise.all([carregarResumo(), carregarTransacoes()]);
}

async function excluirTransacao(id) {
  if (!confirm("Excluir esta transação?")) {
    return;
  }

  const resposta = await fetch(`/transacoes/${id}`, { method: "DELETE" });
  if (resposta.ok) {
    atualizarMes();
  }
}

async function pararFixa(id) {
  const resposta = await fetch(`/transacoes/${id}/fixa`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fixa: false }),
  });

  if (resposta.ok) {
    mensagemFixas.textContent = "Pronto: essa transação não será mais repetida nos próximos meses.";
    atualizarMes();
  }
}

botaoGerarFixas.addEventListener("click", async () => {
  const resposta = await fetch(`/transacoes/gerar-fixas?mes=${inputMes.value}`, {
    method: "POST",
  });

  if (!resposta.ok) {
    mensagemFixas.textContent = "Não foi possível gerar os gastos fixos.";
    return;
  }

  const dados = await resposta.json();
  mensagemFixas.textContent =
    dados.criadas === 0
      ? "Nenhuma transação fixa nova para gerar neste mês."
      : `${dados.criadas} transação(ões) fixa(s) criada(s) neste mês.`;

  atualizarMes();
});

/* ---------- Metas ---------- */

function textoDaMeta(meta) {
  if (meta.status === "concluida") {
    return "Meta concluída! 🎉";
  }
  if (meta.status === "vencida") {
    return `Prazo vencido em ${formatarData(meta.prazo)}. Ainda faltam ${formatarMoeda(meta.faltante)}.`;
  }
  const unidade = meta.meses_restantes === 1 ? "mês" : "meses";
  return `Faltam ${formatarMoeda(meta.faltante)}. Guarde ${formatarMoeda(meta.guardar_por_mes)} por mês até ${formatarData(meta.prazo)} (${meta.meses_restantes} ${unidade}).`;
}

function criarCartaoMeta(meta) {
  const cartao = criarElemento("div", "meta");
  cartao.appendChild(criarElemento("h3", "", meta.nome));

  const barra = criarElemento("div", "barra");
  const preenchida = criarElemento("div", "barra-preenchida");
  preenchida.style.width = `${meta.progresso}%`;
  barra.appendChild(preenchida);
  cartao.appendChild(barra);

  cartao.appendChild(
    criarElemento(
      "p",
      "meta-valores",
      `${formatarMoeda(meta.valor_guardado)} de ${formatarMoeda(meta.valor_alvo)} (${meta.progresso.toFixed(0)}%)`
    )
  );
  cartao.appendChild(criarElemento("p", "meta-info", textoDaMeta(meta)));

  const acoes = criarElemento("div", "meta-acoes");

  const campo = criarElemento("input");
  campo.type = "number";
  campo.step = "0.01";
  campo.min = "0.01";
  campo.placeholder = "Valor guardado";

  const botaoGuardar = criarElemento("button", "", "Guardar");
  botaoGuardar.type = "button";
  botaoGuardar.addEventListener("click", () => depositar(meta.id, campo.value));

  const botaoExcluir = criarElemento("button", "secundario", "Excluir");
  botaoExcluir.type = "button";
  botaoExcluir.addEventListener("click", () => excluirMeta(meta.id));

  acoes.appendChild(campo);
  acoes.appendChild(botaoGuardar);
  acoes.appendChild(botaoExcluir);
  cartao.appendChild(acoes);

  return cartao;
}

async function carregarMetas() {
  const resposta = await fetch("/metas/");
  const metas = await resposta.json();

  listaMetas.replaceChildren();
  avisoSemMetas.hidden = metas.length > 0;

  for (const meta of metas) {
    listaMetas.appendChild(criarCartaoMeta(meta));
  }
}

async function depositar(id, valor) {
  const numero = parseFloat(valor);
  if (!numero || numero <= 0) {
    return;
  }

  const resposta = await fetch(`/metas/${id}/depositar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ valor: numero }),
  });

  if (resposta.ok) {
    carregarMetas();
  }
}

async function excluirMeta(id) {
  if (!confirm("Excluir esta meta?")) {
    return;
  }

  const resposta = await fetch(`/metas/${id}`, { method: "DELETE" });
  if (resposta.ok) {
    carregarMetas();
  }
}

formMeta.addEventListener("submit", async (evento) => {
  evento.preventDefault();

  const corpo = {
    nome: document.getElementById("meta-nome").value,
    valor_alvo: parseFloat(document.getElementById("meta-alvo").value),
    valor_guardado: parseFloat(document.getElementById("meta-guardado").value) || 0,
    prazo: document.getElementById("meta-prazo").value,
  };

  const resposta = await fetch("/metas/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(corpo),
  });

  if (resposta.ok) {
    mensagemMeta.textContent = "Meta criada!";
    formMeta.reset();
    carregarMetas();
  } else {
    const erro = await resposta.json();
    mensagemMeta.textContent = mensagemDeErro(erro);
  }
});

/* ---------- Nova transação ---------- */

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
    atualizarMes();
  } else {
    const erro = await resposta.json();
    mensagem.textContent = mensagemDeErro(erro);
  }
});

inputMes.addEventListener("change", () => {
  mensagemFixas.textContent = "";
  atualizarMes();
});

/* ---------- Início ---------- */

inputMes.value = mesAtual();
inputData.value = hojeISO();
atualizarMes();
carregarMetas();