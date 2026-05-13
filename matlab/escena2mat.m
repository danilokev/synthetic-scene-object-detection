% ============================================================
%  ARCHIVO: escena2mat.m
%  Escena 2 – Objetos BLANCOS, cámara FIJA, luz en órbita
%  Mismo algoritmo que escena 1 + filtro de solidez para
%  rechazar sombras alargadas que aparecen en frames tardíos
% ============================================================
clear; clc; close all;

dir_datos  = fullfile('datos',   'escena2');
dir_salida = fullfile('salidas', 'escena2');
if ~exist(dir_salida,'dir'), mkdir(dir_salida); end

secs = {'escena2_1','escena2_2','escena2_3'};

for e = 1:numel(secs)
    nom  = secs{e};
    din  = fullfile(dir_datos,  nom);
    dout = fullfile(dir_salida, [nom '_salida']);
    if ~exist(dout,'dir'), mkdir(dout); end

    arch = dir(fullfile(din,'*.png'));
    if isempty(arch), fprintf('Sin imágenes en %s\n', din); continue; end

    vid = VideoWriter(fullfile(dir_salida, [nom '_salida.mp4']), 'MPEG-4');
    vid.FrameRate = 1; open(vid);

    for k = 1:numel(arch)
        img  = imread(fullfile(din, arch(k).name));
        gris = rgb2gray(img);

        inv = imcomplement(gris);
        T   = max(graythresh(inv), 0.06);
        bw  = imbinarize(inv, T);
        bw  = imopen(bw,  strel('disk', 3));
        bw  = imclose(bw, strel('disk', 8));
        bw  = imfill(bw,  'holes');
        bw  = bwareaopen(bw, 400);

        % Escena 2: la luz lateral crea sombras muy alargadas.
        % La solidez (Area/ConvexArea) es baja para formas irregulares/alargadas
        % → permite descartar sombras sin eliminar objetos reales.
        st = regionprops(bw, 'Centroid','BoundingBox','Area','Perimeter','Solidity');
        io = img; nd = 0;

        for i = 1:numel(st)
            A   = st(i).Area;
            sol = st(i).Solidity;
            if A < 400 || sol < 0.50, continue; end  % rechaza sombras alargadas
            nd = nd + 1;
            cx = st(i).Centroid(1);  cy = st(i).Centroid(2);
            bb = st(i).BoundingBox;  P  = max(st(i).Perimeter, 1);

            circ = 4*pi*A / P^2;
            asp  = bb(3) / max(bb(4), 1);

            if     circ > 0.72,           et = 'Cilindro'; c = 'green';
            elseif asp  > 1.4 || asp < 0.70, et = 'Prisma';   c = 'blue';
            else,                          et = 'Cubo';     c = 'red';
            end

            io = insertShape(io,  'Rectangle', bb, 'Color',c, 'LineWidth',2);
            io = insertMarker(io, [cx cy],      '+', 'Color',c, 'Size',15);
            io = insertText(io,   [cx-30 cy-22], et, 'FontSize',11, ...
                'TextColor',c, 'BoxColor','white', 'BoxOpacity',0.65);
        end

        % El ángulo de la luz va de 90° (cenital) a 0° (lateral)
        ang = 90 - (k-1)*90/max(numel(arch)-1, 1);
        io = insertText(io, [5 5], sprintf('F%d/%d | Luz:%.0f° | Det:%d', ...
            k, numel(arch), ang, nd), ...
            'FontSize',12,'TextColor','black','BoxColor','white','BoxOpacity',0.8);
        imwrite(io, fullfile(dout, arch(k).name));
        writeVideo(vid, io);
    end
    close(vid);
    fprintf(' %s_salida generada\n', nom);
end
fprintf('=== Escena 2 completa ===\n');