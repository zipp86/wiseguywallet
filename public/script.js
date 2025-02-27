const createWalletForm = document.getElementById('create-wallet-form');
const walletList = document.getElementById('wallet-list');
const exchangeForm = document.getElementById('exchange-form');
const balanceDiv = document.getElementById('balance');
const transferForm = document.getElementById('transfer-form');
const transactionsDiv = document.getElementById('transactions');
const logoutForm = document.getElementById('logout-form');

createWalletForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const walletName = document.getElementById('wallet-name').value;
    fetch('/create_wallet', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ wallet_name: walletName })
    })
    .then((response) => response.json())
    .then((data) => {
        const walletId = data.wallet_id;
        walletList.innerHTML += `<p>Wallet ${walletName} created with ID ${walletId}</p>`;
    });
});

exchangeForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const amount = document.getElementById('amount').value;
    fetch('/exchange', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ wallet_id: walletId, amount: amount })
    })
    .then((response) => response.json())
    .then((data) => {
        balanceDiv.innerHTML = `Balance: ${data.balance}`;
    });
});

transferForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const to = document.getElementById('to').value;
    const amount = document.getElementById('amount').value;
    fetch('/transfer', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ wallet_id: walletId, to: to, amount: amount })
    })
    .then((response) => response.json())
    .then((data) => {
        transactionsDiv.innerHTML += `<p>Transaction ${data.transaction_id} to ${to} for ${amount}</p>`;
    });
});

logoutForm.addEventListener('submit', (e) => {
    e.preventDefault();
    fetch('/logout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ wallet_id: walletId })
    })
    .then((response) => response.json())
    .then((data) => {
        console.log('Logged out');
    });
});
