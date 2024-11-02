from diffiehellman.diffiehellman import DiffieHellman

alice = DiffieHellman()
bob = DiffieHellman()

alice.generate_public_key()
bob.generate_public_key()

alices_shared_key = alice.generate_shared_secret(bob.public_key, echo_return_key=True)
bobs_shared_key = bob.generate_shared_secret(alice.public_key, echo_return_key=True)
print(alices_shared_key == bobs_shared_key, alices_shared_key, bobs_shared_key)
