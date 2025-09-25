import requests
print('testing simplify')
res = requests.post('http://127.0.0.1:5000/algebra', json={'action':'simplify','expr':'(x^2-1)/(x-1)'} )
print(res.status_code, res.text)
print('testing solve')
res2 = requests.post('http://127.0.0.1:5000/algebra', json={'action':'solve','expr':'x^2-4'} )
print(res2.status_code, res2.text)
