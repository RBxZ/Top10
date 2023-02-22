import socket
import base64
import pymongo

USERNAME = ""
IP = "192.168.11.1"
PORT = 6900
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((IP, PORT))
server_socket.listen(1)
print("Wating for connection")

# MongoDB Client
client_string = f"mongodb+srv://RBxZ9:rbozi123@top10-db.hciuc4v.mongodb.net/?retryWrites=true&w=majority"

client = pymongo.MongoClient(client_string)

db = client["Top10-DB"]  # Connects to the database
users = db["Users"]  # Connects to the collection

def main():
  while True:
    client_socket, client_address_port = server_socket.accept()
    print("connected.")
    content = "Not_done"
    run = True
    msg_length = 0;
    while run:
      data = client_socket.recv(10240)
      if data:
        print(data)
        msg = base64.b64decode(data.decode()).decode("utf-8")
        while msg[-4:] != "done":
          data += client_socket.recv(10240)
          msg = base64.b64decode(data.decode()).decode("utf-8")
        msg = base64.b64decode(data.decode()).decode("utf-8")
        parameters = msg.split(";")
        for i in range(len(parameters)):
          size = parameters[i][0:5]
          length = int(size)
          parameters[i] = parameters[i][5:length + 5]
        print(parameters)

        #___________________Check Purpose___________________________________
        match parameters[0]:
          case "done":
            client_socket.close()
            run = False
          case "sign_in":
            check = handle_sign_in(parameters[1], parameters[2], parameters[3])
            if check == False:
              client_socket.send(base64.b64encode("Failed".encode()))
            else:
              client_socket.send(base64.b64encode("Success".encode()))
              client_socket.close()
              run = False
          case "log_in":
            check = handle_log_in(parameters[1], parameters[2])
            if check == False:
              client_socket.send(base64.b64encode("Failed".encode()))
            else:
              client_socket.send(base64.b64encode("Success".encode()))
              client_socket.close()
              run = False
          case "add_my_list":
            check = handle_add_my_list(parameters[1:]);
            if check == False:
              client_socket.send(base64.b64encode("Failed".encode()))
            else:
              client_socket.send(base64.b64encode("Success".encode()))
              client_socket.close()
              run = False
          case "edit_my_list":
            check = handle_edit_my_list(parameters[1:]);
            if check == False:
              client_socket.send(base64.b64encode("Failed".encode()))
            else:
              client_socket.send(base64.b64encode("Success".encode()))
              client_socket.close()
              run = False
          case "delete_list":
            check = handle_delete_list(parameters[1])
            if check:
              client_socket.send(base64.b64encode("Deleted".encode()))
              client_socket.close()
              run = False
          case "load_my_lists":
            message = handle_load_my_lists();
            if message:
              client_socket.send(base64.b64encode(message.encode()))
              client_socket.close()
              run = False
            else:
              client_socket.send(base64.b64encode("Failed".encode()))
          case "edit_user":
            check = handle_edit_user(parameters[1], parameters[2], parameters[3])
            if check == False:
              client_socket.send(base64.b64encode("Failed".encode()))
            else:
              client_socket.send(base64.b64encode("Success".encode()))
              client_socket.close()
              run = False




def handle_sign_in(username, password, user_image):
  #___________________Check thet does not exist and add to DB_________________________________
  existing_users = users.find({
    "username" : username
  }, {
    "name": True
  })
  existing_users = list(existing_users)
  if len(existing_users) != 0:
    return False
  else:
    imgdata = base64.b64decode(user_image)
    filename = 'user_image.jpg'
    with open(filename, 'wb') as f:
      f.write(imgdata)
    with open("user_image.jpg", "rb") as image_file:
      encoded_string = base64.b64encode(image_file.read())
    new_user = {
      "username": username,
      "password": password,
      "user_image":encoded_string,
      "lists":[]
    }
    users.insert_one(new_user)
    globals()["USERNAME"] = username
  return True

def handle_log_in(username, password):
  existing_users = users.find({
    "username": username,
    "password": password
  }, {
    "name": True,
    "password": True
  })
  existing_users = list(existing_users)
  if len(existing_users) != 0:
    globals()["USERNAME"] = username
    return True
  return False

def handle_add_my_list(parameters):
  username = globals()["USERNAME"]
  user = users.find_one({"username": username})
  lists = user.get("lists")
  for list in lists:
      list_name = list.get("list_name")
      if list_name == parameters[0]:
        return False
  query = {"username": username}
  new_list = {
    "$push": {
      "lists": {
        "list_name": parameters[0],
        "list_description": parameters[1],
        "list_image": parameters[2],
        "items": [
          {"item_name": parameters[i], "item_description": parameters[i + 1], "item_image": parameters[i + 2]}
          for i in range(3, len(parameters) - 3, 3)
        ]
      }
    }
  }
  users.update_one(query, new_list)
  return True

def handle_edit_my_list(parameters):
  username = globals()["USERNAME"]
  user = users.find_one({"username": username})
  lists = user.get("lists")
  for list in lists:
    list_name = list.get("list_name")
    if list_name == parameters[1]:
      return False
  query = {"username": username, "lists.list_name": parameters[0]}
  new_list = {
    "$set": {
        "lists.$.list_name": parameters[1],
        "lists.$.list_description": parameters[2],
        "lists.$.list_image": parameters[3],
        "lists.$.items": [
          {"lists.$.items.item_name": parameters[i], "lists.$.items.item_description": parameters[i + 1], "lists.$.items.item_image": parameters[i + 2]}
          for i in range(4, len(parameters) - 4, 3)
        ]
    }
  }
  users.find_one_and_update (query, new_list)
  return True;


def handle_delete_list(list_name):
  username = globals()["USERNAME"]
  user = users.find_one({"username":username})
  users.update_one({"username":username}, {"$pull":{"lists":{"list_name":list_name}}})
  return True

def handle_load_my_lists():
  username = globals()["USERNAME"]
  user = users.find_one({"username": username})
  print(user)
  lists = user.get("lists")
  message = ""
  for list in lists:
    list_name = list.get("list_name")
    list_description = list.get("list_description")
    list_image = list.get("list_image")
    all_items = ""
    items = list.get("items")
    for item in items:
      item_name = item.get("item_name")
      item_description = item.get("item_description")
      item_image = item.get("item_image")
      all_items = all_items + item_name + ";" +  item_description + ";" + item_image + ";"
    message = message +  list_name + ";"  + list_description + ";"  + list_image + ";"
    message += all_items
  message += "done"
  print(message)
  return message

def handle_edit_user(new_username, new_password, new_image):
  existing_users = users.find({
    "username": new_username
  }, {
    "name": True
  })
  existing_users = list(existing_users)
  if len(existing_users) != 0:
    return False
  username = globals()["USERNAME"]
  if new_image == "false":
    users.find_one_and_update({"username": username}, {"$set": {"username":new_username, "password":new_password}})
  else:
    users.find_one_and_update({"username": username}, {"$set": {"username": new_username, "password": new_password, "user_image": new_image}})
  globals()["USERNAME"] = username
  return True


def pad_with_zeros(number, length):
  padded = str(number).zfill(length)
  return padded
if __name__ == "__main__":
  main()
