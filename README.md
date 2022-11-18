## Local Dev

For the local development the `in/` and `out/` directories are used. Please .aax file in the `in/` directory and the .mp3s will be created in the `out/` directory.

1. Building the image
```docker build -t audible-processor .```

2. Run the watcher using the following command:
```docker run --rm --name audible-processor -it -v "${PWD}/in:/aax" -v "${PWD}/out:/mp3" audible-processor watch -vvv -o /mp3 /aax```

The watcher will now pause and poll for the auth file to exist before trying to do anything.

3. Authenticate with audible
```docker exec -it audible-processor auth -o /mp3```

The `-o` option is required so the `.auth` file is saved to the correct location. You should only have to do this once, because the `.auth` file will be saved to the local disk. All subsequent runs of the container will see it and use those activation bytes.

If you need to change accounts, you will need to stop the running container, delete the `./out/.auth` file, then redo step 3.

## Pushing to hub

1. Login
```docker login```
Make sure that if you are using a token, the token has appropriate access.

2. Build the image
See step 1 in Local Dev

3. Tag the image with the new version and as latest
```
docker tag audible-processor drductus/audible-processor:vx.x.x
docker tag audible-processor drductus/audible-processor:latest
```

4. Push the tags
```
docker push drductus/audible-processor:vx.x.x
docker push drductus/audible-processor:latest
```

5. Update the pub README with any additional instructions
