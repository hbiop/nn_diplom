def create_model(*, form, user, layers):
    model = form.save(commit=False)
    model.parameters = {'layers': layers}
    model.user = user
    model.save()
    return model


def collect_layers(post_data, layer_form_class):
    layer_fields = [
        key for key in post_data
        if key.startswith('layer_') and '-units' in key
    ]
    layer_indices = sorted({
        int(key.split('_')[1].split('-')[0]) for key in layer_fields
    })

    layers = []
    valid = True
    for index in layer_indices:
        prefix = f'layer_{index}'
        layer_form = layer_form_class({
            f'{prefix}-units': post_data.get(f'{prefix}-units'),
            f'{prefix}-activation': post_data.get(f'{prefix}-activation'),
        }, prefix=prefix)
        if layer_form.is_valid():
            layers.append({
                'size': layer_form.cleaned_data['units'],
                'activation': layer_form.cleaned_data['activation'],
            })
        else:
            valid = False
    return layers, valid
